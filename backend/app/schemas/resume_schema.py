from pydantic import BaseModel, Field


class Education(BaseModel):

    degree: str | None = None
    institution: str | None = None
    graduation_year: str | None = None


class Experience(BaseModel):

    job_title: str | None = None
    company: str | None = None
    duration: str | None = None
    responsibilities: list[str] = Field(default_factory=list)


class Project(BaseModel):

    project_name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ResumeData(BaseModel):

    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None

    technical_skills: list[str] = Field(default_factory=list)

    education: list[Education] = Field(default_factory=list)

    experience: list[Experience] = Field(default_factory=list)

    projects: list[Project] = Field(default_factory=list)

    certifications: list[str] = Field(default_factory=list)