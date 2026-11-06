from pydantic import BaseModel, Field, field_validator


class JobDescription(BaseModel):

    job_title: str = Field(
        min_length=2,
        description="Title of the job"
    )

    company_name: str | None = None

    job_description: str = Field(
        min_length=50,
        description="Full job description"
    )

    # Clean unnecessary spaces before validation
    @field_validator("job_title", "job_description", "company_name", mode="before")
    @classmethod
    def clean_whitespace(cls, value):

        if isinstance(value, str):
            return value.strip()

        return value

    # Reject empty or whitespace-only values
    @field_validator("job_title", "job_description","company_name")
    @classmethod
    def validate_not_empty(cls, value):

        if not value.strip():
            raise ValueError("This field cannot contain only spaces.")

        return value