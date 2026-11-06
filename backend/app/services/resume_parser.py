from pypdf import PdfReader
from docx import Document
from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes) -> str:

    pdf_reader = PdfReader(BytesIO(file_bytes))

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
            for cell in row.cells:
                extracted_text += cell.text + " "
            extracted_text += "\n"

    return extracted_text