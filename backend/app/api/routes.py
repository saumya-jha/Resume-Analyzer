import asyncio

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.core.errors import UnprocessableInputError
from app.schemas.job_schema import JobDescription
from app.services.job_analyzer import analyze_job_description
from app.services.matching_service import match_resume_with_job
from app.services.resume_analyzer import analyze_resume
from app.services.resume_upload import parse_resume_upload

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
    return {
        "message": "Job description received successfully",
        "job_details": job.model_dump()
    }


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    filename, extracted_text = await parse_resume_upload(file)

    return {
        "message": "Resume uploaded successfully!",
        "filename": filename,
        "content_type": file.content_type,
        "extracted_text": extracted_text
    }


@router.post("/analyze-job")
async def analyze_job(job: JobDescription):

    # The AI call is blocking, so it runs in a worker thread and does not
    # freeze the server for other users while it waits.
    requirements = await run_in_threadpool(
        analyze_job_description,
        job.job_description
    )

    return {
        "message": "Job description analyzed successfully!",
        "job_title": job.job_title,
        "company_name": job.company_name,
        "requirements": requirements.model_dump()
    }


@router.post("/analyze-resume")
async def analyze_uploaded_resume(file: UploadFile = File(...)):

    filename, extracted_text = await parse_resume_upload(file)

    resume_data = await run_in_threadpool(analyze_resume, extracted_text)

    return {
        "message": "Resume analyzed successfully!",
        "filename": filename,
        "resume": resume_data.model_dump()
    }


@router.post("/analyze-match")
async def analyze_match(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    company_name: str | None = Form(None)
):

    # Validate the job details
    try:
        job = JobDescription(
            job_title=job_title,
            company_name=company_name,
            job_description=job_description
        )
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
            for err in error.errors()
        )
        raise UnprocessableInputError(problems)

    # Validate the resume and extract its text
    filename, extracted_text = await parse_resume_upload(file)

    # The resume and the job description are independent, so analyze both
    # at the same time instead of one after the other.
    resume_data, job_requirements = await asyncio.gather(
        run_in_threadpool(analyze_resume, extracted_text),
        run_in_threadpool(analyze_job_description, job.job_description),
    )

    if not job_requirements.required_skills:
        raise UnprocessableInputError(
            "No skills could be found in the job description. Please paste "
            "the full description, including its requirements section."
        )

    matching_result = match_resume_with_job(resume_data, job_requirements)

    return {
        "message": "Resume and job matching completed successfully!",
        "candidate_name": resume_data.candidate_name,
        "filename": filename,
        "job_title": job.job_title,
        "company_name": job.company_name,
        "matching_result": matching_result.model_dump(),
        "resume": resume_data.model_dump(),
        "job_requirements": job_requirements.model_dump()
    }
