from pydantic import BaseModel, Field, field_validator


class JobDescription(BaseModel):

    job_title: str = Field(
        min_length=2,
        max_length=200,
        description="Title of the job"
    )

    # Optional. A blank value (for example an empty form field) means "none".
    company_name: str | None = Field(
        default=None,
        max_length=200,
    )

    job_description: str = Field(
        min_length=50,
        max_length=20000,
        description="Full job description"
    )

    # Remove surrounding spaces before the length rules are checked, so a
    # value made only of spaces is rejected by min_length.
    @field_validator("job_title", "job_description", mode="before")
    @classmethod
    def strip_whitespace(cls, value):

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("company_name", mode="before")
    @classmethod
    def blank_company_is_none(cls, value):

        if isinstance(value, str):
            value = value.strip()

        return value or None
