from app.services.resume_parser import extract_text_from_pdf
from app.services.resume_parser import extract_text_from_docx
from app.services.job_analyzer import analyze_job_description
from app.services.matching_service import match_resume_with_job
from app.services.resume_analyzer import analyze_resume
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.schemas.job_schema import JobDescription
from pathlib import Path


router = APIRouter()

@router.get("/")
def home():
    return {
        "message": "Welcome to Resume Analyzer",
        "status": "Application is running successfully"
    }

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Resume Analyzer"
    }

@router.post("/jobs")
def create_job(job: JobDescription):
    return{
        "message": "Job description received successfully",
        "job_details": job.model_dump()
    }

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    # Get the file extension
    file_extension = Path(file.filename).suffix.lower()

    # Allow only PDF and DOCX
    allowed_extensions = [".pdf", ".docx"]

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    # Read uploaded file
    contents = await file.read()

    # Validate actual file signature
    if file_extension == ".pdf":
        if not contents.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file. The file content does not match its extension."
            )

    elif file_extension == ".docx":
        if not contents.startswith(b"PK"):
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file. The file content does not match its extension."
            )

    # Extract text with error handling
    try:
        if file_extension == ".pdf":
            extracted_text = extract_text_from_pdf(contents)

        elif file_extension == ".docx":
            extracted_text = extract_text_from_docx(contents)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the file. It may be corrupted or invalid."
        )
    # Check whether text was extracted
    if not extracted_text.strip():
        raise HTTPException(
        status_code=400,
        detail="No readable text found in the resume."
    )

    return {
        "message": "Resume uploaded successfully!",
        "filename": file.filename,
        "content_type": file.content_type,
        "extracted_text": extracted_text
    }

@router.post("/analyze-job")
def analyze_job(job: JobDescription):

    try:
        requirements = analyze_job_description(
            job.job_description
        )

        return {
            "message": "Job description analyzed successfully!",
            "job_title": job.job_title,
            "company_name": job.company_name,
            "requirements": requirements.model_dump()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Job analysis failed: {str(e)}"
        )

@router.post("/analyze-resume")
async def analyze_uploaded_resume(file: UploadFile = File(...)):

    # Get the file extension
    file_extension = Path(file.filename).suffix.lower()

    # Allow only PDF and DOCX files
    if file_extension not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    # Read the uploaded file
    contents = await file.read()

    # Check whether the file format is valid
    if file_extension == ".pdf" and not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file."
        )

    if file_extension == ".docx" and not contents.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail="Invalid DOCX file."
        )

    # Extract text from the resume
    try:
        if file_extension == ".pdf":
            extracted_text = extract_text_from_pdf(contents)
        else:
            extracted_text = extract_text_from_docx(contents)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the uploaded resume."
        )

    # Check whether text was extracted
    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the resume."
        )

    # Analyze the extracted resume text using Groq
    try:
        resume_data = analyze_resume(extracted_text)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Resume analysis failed: {str(e)}"
        )

    return {
        "message": "Resume analyzed successfully!",
        "filename": file.filename,
        "resume": resume_data.model_dump()
    }

@router.post("/analyze-match")
async def analyze_match(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    company_name: str | None = Form(None)
):

    # Validate job details
    try:
        job = JobDescription(
            job_title=job_title,
            company_name=company_name,
            job_description=job_description
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Validate resume file
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    contents = await file.read()

    if file_extension == ".pdf" and not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    if file_extension == ".docx" and not contents.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="Invalid DOCX file.")

    # Extract resume text
    try:
        if file_extension == ".pdf":
            extracted_text = extract_text_from_pdf(contents)
        else:
            extracted_text = extract_text_from_docx(contents)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the uploaded resume."
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the resume."
        )

    # Analyze resume
    try:
        resume_data = analyze_resume(extracted_text)

        # Analyze job description
        job_requirements = analyze_job_description(
            job.job_description
        )

        # Match resume with job
        matching_result = match_resume_with_job(
            resume_data,
            job_requirements
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Matching analysis failed: {str(e)}"
        )

    return {
        "message": "Resume and job matching completed successfully!",
        "candidate_name": resume_data.candidate_name,
        "job_title": job.job_title,
        "company_name": job.company_name,
        "matching_result": matching_result.model_dump()
    }