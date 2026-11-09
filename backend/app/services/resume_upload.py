"""Validates an uploaded resume and extracts its text.

Used by every endpoint that accepts a resume, so the rules live in one place:
file name, extension, size, real file type, readable text.
"""

import logging
import re
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.errors import AppError, FileTooLargeError, FileValidationError
from app.services.resume_parser import (
    extract_text_from_docx,
    extract_text_from_pdf,
)

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# A DOCX is a zip file; refuse ones that would expand to something enormous
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024


def safe_filename(raw_name: str | None) -> str:
    """Return only the file name: no folders, no control characters."""

    name = re.split(r"[\\/]", raw_name or "")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()

    return name[:200]


def _check_file_signature(extension: str, contents: bytes) -> None:
    """Make sure the file really is what its extension claims."""

    if extension == ".pdf":

        if not contents.startswith(b"%PDF-"):
            raise FileValidationError(
                "Invalid PDF file. The file content does not match its extension."
            )

        return

    try:
        with zipfile.ZipFile(BytesIO(contents)) as archive:

            if "word/document.xml" not in archive.namelist():
                raise zipfile.BadZipFile

            uncompressed = sum(info.file_size for info in archive.infolist())

            if uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                raise FileValidationError(
                    "This DOCX file is too large once unpacked."
                )

    except zipfile.BadZipFile:
        raise FileValidationError(
            "Invalid DOCX file. The file content does not match its extension."
        )


def _extract(extension: str, contents: bytes) -> str:

    if extension == ".pdf":
        return extract_text_from_pdf(contents)

    return extract_text_from_docx(contents)


async def parse_resume_upload(file: UploadFile) -> tuple[str, str]:
    """Validate the upload and return (file name, extracted text)."""

    filename = safe_filename(file.filename)

    if not filename:
        raise FileValidationError("Please choose a resume file to upload.")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError("Only PDF and DOCX files are allowed.")

    # Read one byte more than allowed so oversized files are detected
    # without loading the whole thing into memory.
    contents = await file.read(settings.max_upload_bytes + 1)

    if len(contents) > settings.max_upload_bytes:
        raise FileTooLargeError(
            f"The file is too large. Maximum size is {settings.max_upload_mb} MB."
        )

    if not contents:
        raise FileValidationError("The uploaded file is empty.")

    _check_file_signature(extension, contents)

    try:
        text = await run_in_threadpool(_extract, extension, contents)

    except AppError:
        raise

    except Exception:
        logger.warning("Could not parse uploaded resume", exc_info=True)
        raise FileValidationError(
            "Unable to read the file. It may be corrupted or invalid."
        )

    text = text.replace("\x00", " ")

    if not text.strip():
        raise FileValidationError(
            "No readable text found in the resume. If it is a scanned image "
            "or photo, please upload a text-based PDF or a DOCX instead."
        )

    return filename, text
