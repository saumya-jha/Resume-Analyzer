from pydantic import BaseModel, Field


class SkillMatching(BaseModel):

    matched_skills: list[str] = Field(default_factory=list)

    missing_skills: list[str] = Field(default_factory=list)

    partially_matched_skills: list[str] = Field(default_factory=list)


class ProjectMatching(BaseModel):

    relevant_projects: list[str] = Field(default_factory=list)

    relevance_explanation: list[str] = Field(default_factory=list)


class EducationMatching(BaseModel):
    """Explains how the education score was reached."""

    required_level: str | None = None

    candidate_level: str | None = None

    required_fields: list[str] = Field(default_factory=list)

    candidate_fields: list[str] = Field(default_factory=list)

    # True / False when known, None when the level could not be determined
    level_met: bool | None = None

    # not_required | unknown | match | related | adjacent | unrelated
    field_relevance: str | None = None

    explanation: str = ""


class MatchingResult(BaseModel):

    overall_score: float = Field(ge=0, le=100)

    skill_score: float = Field(ge=0, le=100)

    project_score: float = Field(ge=0, le=100)

    experience_score: float = Field(ge=0, le=100)

    education_score: float = Field(ge=0, le=100)

    skill_matching: SkillMatching

    project_matching: ProjectMatching

    education_matching: EducationMatching = Field(
        default_factory=EducationMatching
    )

    strengths: list[str] = Field(default_factory=list)

    improvement_suggestions: list[str] = Field(default_factory=list)