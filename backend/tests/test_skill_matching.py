import pytest

from app.services.skill_matching import (
    expand_listed_skills,
    match_skills,
    normalize_skill,
    split_compound,
    unique_required_skills,
    calculate_skill_score,
)


# ---- normalisation -------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("Node", "node.js"),
    ("NodeJS", "node.js"),
    ("Node.js", "node.js"),
    ("node js", "node.js"),
    ("React.js", "react"),
    ("ReactJS", "react"),
    ("Postgres", "postgresql"),
    ("Postgres SQL", "postgresql"),
    ("Spring-Boot", "spring boot"),
    ("SpringBoot", "spring boot"),
    ("JS", "javascript"),
    ("K8s", "kubernetes"),
    ("HTML5", "html"),
    ("Mongo", "mongodb"),
    ("Amazon Web Services", "aws"),
    ("C++", "c++"),
    ("C#", "c#"),
    (".NET", ".net"),
    ("CI/CD", "ci/cd"),
    ("  Python  ", "python"),
    ("Python (Flask)", "python"),
    ("Some Unknown Tool", "some unknown tool"),
])
def test_normalize_skill(raw, expected):
    assert normalize_skill(raw) == expected


def test_split_compound_skills():
    assert split_compound("HTML/CSS") == ["HTML", "CSS"]
    assert split_compound("CI/CD") == ["CI/CD"]
    assert split_compound("PL/SQL") == ["PL/SQL"]
    assert split_compound("Python") == ["Python"]


def test_expand_listed_skills_handles_combined_entries():
    skills = expand_listed_skills(
        ["Python, Java", "HTML/CSS", "Python (Flask, Django)"]
    )

    assert {"python", "java", "html", "css", "flask", "django"} <= skills


# ---- full / partial / missing --------------------------------------------

def result(candidate, required, text=""):
    return match_skills(candidate, required, text)


def test_exact_match_under_different_spellings():
    r = result(["NodeJS", "Postgres"], ["Node.js", "PostgreSQL"])

    assert r.matched_skills == ["Node.js", "PostgreSQL"]
    assert r.missing_skills == []


def test_specific_skill_implies_general_skill():
    assert result(["MySQL"], ["SQL"]).matched_skills == ["SQL"]
    assert result(["Spring Boot"], ["Java"]).matched_skills == ["Java"]
    assert result(["Flask"], ["Python"]).matched_skills == ["Python"]
    assert result(["Express"], ["JavaScript", "Node.js"]).matched_skills == [
        "JavaScript", "Node.js"
    ]


def test_implication_chains_through_several_levels():
    # MySQL -> SQL -> databases
    assert result(["MySQL"], ["Databases"]).matched_skills == ["Databases"]


def test_general_skill_gives_only_partial_credit_for_specific_one():
    assert result(["Java"], ["Spring Boot"]).partially_matched_skills == [
        "Spring Boot"
    ]
    assert result(["SQL"], ["MySQL"]).partially_matched_skills == ["MySQL"]
    assert result(["Python"], ["Django"]).partially_matched_skills == ["Django"]


def test_sibling_technologies_give_partial_credit():
    assert result(["AWS"], ["Azure"]).partially_matched_skills == ["Azure"]
    assert result(["Flask"], ["Django"]).partially_matched_skills == ["Django"]
    assert result(["React"], ["Vue"]).partially_matched_skills == ["Vue"]
    assert result(["PostgreSQL"], ["MySQL"]).partially_matched_skills == [
        "MySQL"
    ]


def test_unrelated_skills_are_missing():
    r = result(["Java"], ["Kubernetes", "Tableau"])

    assert r.missing_skills == ["Kubernetes", "Tableau"]


def test_java_and_javascript_are_never_confused():
    assert result(["Java"], ["JavaScript"]).missing_skills == ["JavaScript"]
    assert result(["JavaScript"], ["Java"]).missing_skills == ["Java"]


def test_compound_required_skill():
    r = result(["HTML", "CSS"], ["HTML/CSS"])
    assert r.matched_skills == ["HTML/CSS"]

    r = result(["HTML"], ["HTML/CSS"])
    assert r.partially_matched_skills == ["HTML/CSS"]

    r = result(["HTML/CSS"], ["HTML", "CSS"])
    assert r.matched_skills == ["HTML", "CSS"]


# ---- evidence from free text ---------------------------------------------

def test_skill_mentioned_in_text_counts_even_if_not_listed():
    r = result([], ["Docker"], "Deployed the service using Docker.")

    assert r.matched_skills == ["Docker"]


def test_mention_in_text_also_triggers_implications():
    r = result([], ["SQL"], "Built the backend with MySQL.")

    assert r.matched_skills == ["SQL"]


def test_text_search_uses_whole_words():
    r = result([], ["Java"], "Built interactive pages with JavaScript.")

    assert r.missing_skills == ["Java"]


def test_ordinary_english_words_do_not_count_as_skills():
    r = result([], ["Excel", "Spring", "Express", "Go"],
               "I excel at teamwork, in spring semester I did express delivery "
               "and will go far.")

    assert r.missing_skills == ["Excel", "Spring", "Express", "Go"]


# ---- duplicates and scoring ----------------------------------------------

def test_duplicate_required_skills_are_counted_once():
    assert unique_required_skills(["Java", "java", "Core Java"]) == ["Java"]

    r = result(["Java"], ["Java", "java", "Core Java"])

    assert r.matched_skills == ["Java"]
    assert calculate_skill_score(r) == 100.0


def test_skill_score_weights_partial_matches_by_half():
    r = result(["Java"], ["Java", "Spring Boot", "Kubernetes", "Tableau"])

    # 1 full + 1 partial (Spring Boot) + 2 missing -> (1 + 0.5) / 4
    assert calculate_skill_score(r) == 37.5


def test_no_required_skills_scores_full():
    assert calculate_skill_score(result(["Java"], [])) == 100.0


# ---- generic skill names used in real job descriptions --------------------

def test_apis_are_proven_by_api_frameworks():
    assert result(["FastAPI"], ["APIs"]).matched_skills == ["APIs"]
    assert result(["Flask"], ["APIs"]).matched_skills == ["APIs"]
    assert result(["GraphQL"], ["APIs"]).matched_skills == ["APIs"]


def test_apis_are_proven_by_a_project_description():
    r = result([], ["APIs"], "Integrated live weather data via OpenWeatherMap API")

    assert r.matched_skills == ["APIs"]


def test_relational_and_nosql_databases_from_specific_databases():
    r = result(["PostgreSQL", "MongoDB"],
               ["Relational databases", "NoSQL databases"])

    assert r.matched_skills == ["Relational databases", "NoSQL databases"]


def test_sql_alone_proves_relational_databases_but_not_nosql():
    r = result(["SQL"], ["Relational databases", "NoSQL databases"])

    assert r.matched_skills == ["Relational databases"]
    assert r.missing_skills == ["NoSQL databases"]


def test_llm_work_is_recognised():
    assert result(["Gemini AI"], ["LLM development"]).matched_skills == [
        "LLM development"
    ]
    assert result(["OpenAI"], ["LLMs"]).matched_skills == ["LLMs"]
    assert result([], ["LLM development"],
                  "Integrated Google Gemini for complaint classification"
                  ).matched_skills == ["LLM development"]


def test_machine_learning_gives_partial_llm_credit():
    r = result(["Machine Learning"], ["LLM development"])

    assert r.partially_matched_skills == ["LLM development"]


def test_javascript_gives_partial_typescript_credit():
    assert result(["JavaScript"], ["TypeScript"]).partially_matched_skills == [
        "TypeScript"
    ]


# ---- "A or B or C" alternatives ------------------------------------------

def test_any_one_alternative_is_enough():
    r = result(["Azure"], ["AWS or Azure or GCP"])

    assert r.matched_skills == ["AWS or Azure or GCP"]


def test_alternatives_with_only_a_related_skill_are_partial():
    r = result(["Vercel"], ["AWS or Azure or GCP"])

    assert r.partially_matched_skills == ["AWS or Azure or GCP"]


def test_alternatives_with_nothing_related_are_missing():
    r = result(["Java"], ["AWS or Azure or GCP"])

    assert r.missing_skills == ["AWS or Azure or GCP"]


def test_alternatives_count_as_one_skill_in_the_score():
    r = result(["Python"], ["Python", "AWS or Azure or GCP"])

    assert calculate_skill_score(r) == 50.0


# ---- the AI words skills differently from run to run ----------------------

@pytest.mark.parametrize("wording", [
    "LLM development",
    "LLM-based system development",
    "LLM applications",
    "Large Language Model engineering",
    "LLMs",
])
def test_any_llm_wording_is_the_same_skill(wording):
    assert normalize_skill(wording) == "llm"
    assert match_skills(["Gemini AI"], [wording]).matched_skills == [wording]


def test_ai_coding_tools_with_named_examples():
    required = "AI coding tools (Claude Code, Cursor, Codex)"

    assert match_skills(["Cursor"], [required]).matched_skills == [required]
    assert match_skills(["GitHub Copilot"], [required]).matched_skills == [required]
    assert match_skills(["Java"], [required]).missing_skills == [required]
