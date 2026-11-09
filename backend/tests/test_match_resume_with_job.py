from app.schemas.requirements_schema import JobRequirements
from app.schemas.resume_schema import Education, ResumeData
from app.services.matching_service import WEIGHTS, match_resume_with_job


def test_weights_add_up_to_one():
    assert round(sum(WEIGHTS.values()), 6) == 1.0


def test_strong_candidate_scores_high(strong_resume, backend_job):
    result = match_resume_with_job(strong_resume, backend_job)

    # Java, Spring Boot and SQL (via MySQL) match; REST APIs only through
    # the experience description / related frameworks.
    assert result.overall_score >= 85
    assert result.education_score == 100.0
    assert result.experience_score == 100.0
    assert "Java" in result.skill_matching.matched_skills
    assert "SQL" in result.skill_matching.matched_skills
    assert result.skill_matching.missing_skills == []


def test_overall_score_is_the_weighted_sum(strong_resume, backend_job):
    result = match_resume_with_job(strong_resume, backend_job)

    expected = round(
        result.skill_score * 0.50
        + result.project_score * 0.25
        + result.experience_score * 0.15
        + result.education_score * 0.10,
        2,
    )

    assert result.overall_score == expected


def test_all_scores_stay_between_0_and_100(strong_resume, backend_job):
    result = match_resume_with_job(strong_resume, backend_job)

    for value in (
        result.overall_score,
        result.skill_score,
        result.project_score,
        result.experience_score,
        result.education_score,
    ):
        assert 0 <= value <= 100


def test_weak_candidate_scores_low_with_useful_suggestions(backend_job):
    resume = ResumeData(
        technical_skills=["Photoshop"],
        education=[Education(degree="B.Com")],
    )

    job = backend_job.model_copy(update={
        "experience_requirement": "3+ years",
    })

    result = match_resume_with_job(resume, job)

    assert result.overall_score < 25
    assert set(result.skill_matching.missing_skills) == {
        "Java", "Spring Boot", "SQL", "REST APIs"
    }

    suggestions = " ".join(result.improvement_suggestions)

    assert "Missing skills" in suggestions
    assert "3+ years" in suggestions
    assert "Add or expand a project" in suggestions


def test_education_explanation_is_included(strong_resume, backend_job):
    result = match_resume_with_job(strong_resume, backend_job)

    assert result.education_matching.level_met is True
    assert "meets the requirement" in result.education_matching.explanation


def test_education_gap_produces_a_suggestion(backend_job):
    resume = ResumeData(
        technical_skills=["Java"],
        education=[Education(degree="Diploma in Computer Science")],
    )

    result = match_resume_with_job(resume, backend_job)

    assert any(
        "bachelor's degree" in suggestion
        for suggestion in result.improvement_suggestions
    )


def test_skill_found_only_in_experience_text_is_credited(backend_job):
    resume = ResumeData.model_validate({
        "technical_skills": ["Java", "Spring Boot", "SQL"],
        "experience": [{
            "job_title": "Developer",
            "duration": "1 year",
            "responsibilities": ["Designed REST APIs for the billing system"],
        }],
    })

    result = match_resume_with_job(resume, backend_job)

    assert "REST APIs" in result.skill_matching.matched_skills


def test_perfect_candidate_gets_the_fallback_suggestion():
    resume = ResumeData(
        technical_skills=["Python"],
        education=[Education(degree="B.Tech", field_of_study="Computer Science")],
    )
    job = JobRequirements(required_skills=["Python"])

    result = match_resume_with_job(resume, job)

    # No project in the resume, so the project part is the only gap.
    assert result.skill_score == 100.0
    assert result.improvement_suggestions
