
from app.schemas.job_schema import JobDescription

job = JobDescription(
    job_title="Junior AI Engineer",
    company_name="Google",
    job_description="We are looking for a Python developer with experience in AI, machine learning, FastAPI and LLM integration."
)

print(job)
print(job.model_dump())
