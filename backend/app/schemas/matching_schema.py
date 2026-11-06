from pydantic import BaseModel, Field


class SkillMatching(BaseModel):

    matched_skills: list[str] = Field(default_factory=list)

    missing_skills: list[str] = Field(default_factory=list)

    partially_matched_skills: list[str] = Field(default_factory=list)


class ProjectMatching(BaseModel):

    relevant_projects: list[str] = Field(default_factory=list)

    relevance_explanation: list[str] = Field(default_factory=list)


class MatchingResult(BaseModel):

    overall_score: float = Field(ge=0, le=100)

    skill_score: float = Field(ge=0, le=100)

    project_score: float = Field(ge=0, le=100)

    experience_score: float = Field(ge=0, le=100)

    education_score: float = Field(ge=0, le=100)

    skill_matching: SkillMatching

    project_matching: ProjectMatching

    strengths: list[str] = Field(default_factory=list)

    improvement_suggestions: list[str] = Field(default_factory=list)