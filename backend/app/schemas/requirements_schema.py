from pydantic import BaseModel, Field


class JobRequirements(BaseModel):

    required_skills: list[str] = Field(
        default_factory=list,
        description="Technical and other required skills"
    )

    experience_requirement: str | None = None

    education_requirement: str | None = None

    responsibilities: list[str] = Field(
        default_factory=list,
        description="Main responsibilities of the job"
    )