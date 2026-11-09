from app.schemas.resume_schema import Project
from app.services.matching_service import calculate_project_score


def project(name, technologies=None, description=None):
    return Project(
        project_name=name,
        technologies=technologies or [],
        description=description,
    )


def test_project_technologies_are_credited():
    score, details = calculate_project_score(
        [project("Shop", ["Java", "Spring Boot"])],
        ["Java", "Spring Boot"],
    )

    assert score == 100.0
    assert details.relevant_projects == ["Shop"]
    assert "Shop demonstrates: Java, Spring Boot." in details.relevance_explanation


def test_implied_skills_are_credited():
    score, _ = calculate_project_score(
        [project("Shop", ["Spring Boot", "MySQL"])],
        ["Java", "SQL"],
    )

    assert score == 100.0


def test_skill_mentioned_in_description_is_credited():
    score, details = calculate_project_score(
        [project("Chat", description="Real-time chat built with Node.js")],
        ["Node.js"],
    )

    assert score == 100.0
    assert details.relevant_projects == ["Chat"]


def test_description_match_uses_aliases():
    score, _ = calculate_project_score(
        [project("Store", description="Data kept in Postgres")],
        ["PostgreSQL"],
    )

    assert score == 100.0


def test_description_match_uses_whole_words():
    score, _ = calculate_project_score(
        [project("Site", description="A website built with JavaScript")],
        ["Java"],
    )

    assert score == 0.0


def test_related_technology_earns_half_credit():
    score, details = calculate_project_score(
        [project("API", ["Flask"])],
        ["Django"],
    )

    assert score == 50.0
    assert "Related experience with: Django." in details.relevance_explanation[0]


def test_skills_are_combined_across_projects():
    score, details = calculate_project_score(
        [project("A", ["Java"]), project("B", ["Docker"])],
        ["Java", "Docker", "AWS", "Kubernetes"],
    )

    # Java full + Docker full + AWS none + Kubernetes partial (Docker) = 2.5/4
    assert score == 62.5
    assert details.relevant_projects == ["A", "B"]


def test_no_projects_scores_zero():
    score, details = calculate_project_score([], ["Java"])

    assert score == 0.0
    assert details.relevant_projects == []


def test_irrelevant_projects_are_not_listed():
    score, details = calculate_project_score(
        [project("Portfolio", ["HTML", "CSS"])],
        ["Java"],
    )

    assert score == 0.0
    assert details.relevant_projects == []


def test_no_required_skills_scores_full():
    score, _ = calculate_project_score([project("A", ["Java"])], [])

    assert score == 100.0


def test_duplicate_required_skills_do_not_distort_the_score():
    score, _ = calculate_project_score(
        [project("A", ["Java"])],
        ["Java", "java", "Core Java", "AWS"],
    )

    assert score == 50.0
