from io import BytesIO

from docx import Document
from pypdf import PdfReader

from app.core.config import settings
from app.core.errors import FileValidationError


def extract_text_from_pdf(file_bytes: bytes) -> str:

    pdf_reader = PdfReader(BytesIO(file_bytes))

    if pdf_reader.is_encrypted:

        try:
            unlocked = pdf_reader.decrypt("")
        except Exception:
            unlocked = 0

        if not unlocked:
            raise FileValidationError(
                "This PDF is password-protected. "
                "Please upload an unprotected copy."
            )

    if len(pdf_reader.pages) > settings.max_pdf_pages:
        raise FileValidationError(
            f"This PDF has too many pages (maximum {settings.max_pdf_pages}). "
            "Please upload only your resume."
        )

    extracted_text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()

        if page_text:
            extracted_text += page_text + "\n"

    return extracted_text


def extract_text_from_docx(file_bytes: bytes) -> str:

    document = Document(BytesIO(file_bytes))

    extracted_text = ""

    # Extract paragraphs
    for paragraph in document.paragraphs:
        extracted_text += paragraph.text + "\n"

    # Extract tables
    for table in document.tables:
        for row in table.rows:

            seen_cells = set()

            for cell in row.cells:

                # A merged cell is returned once per column it spans;
                # only read it once.
                if id(cell._tc) in seen_cells:
                    continue

                seen_cells.add(id(cell._tc))

                extracted_text += cell.text + " "

            extracted_text += "\n"

    return extracted_text
