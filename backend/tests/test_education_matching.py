import pytest

from app.schemas.resume_schema import Education
from app.services.education_matching import evaluate_education, normalize_text

CS_BACHELORS = "Bachelor's degree in Computer Science"


def score(degree, requirement, field=None):
    value, _ = evaluate_education(
        [Education(degree=degree, field_of_study=field)], requirement
    )
    return value


# ---- equivalent degrees (the main goal of this module) -------------------

@pytest.mark.parametrize("degree", [
    "B.Tech in Computer Science",
    "B.E. in Computer Science",
    "BE Computer Science",
    "B.Sc. in Computer Science",
    "Bachelor of Science in CS",
    "Bachelor's in Computer Science",
    "Bachelor of Technology in CSE",
    "B.E. in CSE",
    "BCA",
])
def test_equivalent_bachelor_degrees_all_score_full(degree):
    assert score(degree, CS_BACHELORS) == 100.0


def test_field_of_study_can_be_a_separate_value():
    assert score("B.Tech", CS_BACHELORS, field="Computer Science") == 100.0


def test_related_computing_field_gets_full_credit():
    assert score("B.Tech in Information Technology", CS_BACHELORS) == 100.0
    assert score("B.Tech in Software Engineering", CS_BACHELORS) == 100.0
    assert score("B.Tech in Artificial Intelligence and Data Science",
                 CS_BACHELORS) == 100.0


# ---- degree levels -------------------------------------------------------

def test_higher_degree_satisfies_lower_requirement():
    assert score("M.Tech Computer Science", CS_BACHELORS) == 100.0
    assert score("PhD in Computer Science", CS_BACHELORS) == 100.0


def test_one_level_below_gets_half_level_credit():
    # level 0.5, field 1.0 -> 75
    assert score("B.Tech in Computer Science",
                 "Master's in Computer Science") == 75.0


def test_two_levels_below_gets_no_level_credit():
    # level 0, field 1.0 -> 50
    assert score("12th Science", CS_BACHELORS) <= 25.0
    assert score("Diploma in Computer Science", "PhD in Computer Science") == 50.0


def test_either_level_requirement_uses_the_lowest():
    assert score("B.Tech CSE", "Bachelor's or Master's degree") == 100.0


def test_plain_degree_requirement_means_bachelors():
    assert score("B.Com", "Any degree") == 100.0
    assert score("Diploma in IT", "A degree in a related field") < 100.0


def test_diploma_accepted_when_requirement_allows_it():
    assert score("Diploma in Computer Engineering",
                 "Diploma or degree in IT") == 100.0


# ---- fields of study -----------------------------------------------------

def test_unrelated_field_loses_field_credit():
    assert score("BBA", CS_BACHELORS) == 50.0
    assert score("MBA", "Master's in Computer Science") == 50.0


def test_neighbouring_stem_field_gets_partial_credit():
    assert score("B.Tech in Electronics and Communication Engineering",
                 CS_BACHELORS) == 75.0


def test_related_field_wording_is_more_lenient():
    strict = score("B.Tech ECE", CS_BACHELORS)
    lenient = score("B.Tech ECE",
                    "Bachelor's degree in Computer Science or related field")

    assert lenient > strict


def test_any_engineering_discipline_accepts_other_engineering():
    assert score("B.Tech Mechanical Engineering",
                 "B.Tech/B.E. in any engineering discipline") == 100.0


def test_degree_without_a_branch_gets_benefit_of_the_doubt():
    # level matches, field unknown -> 75
    assert score("B.Tech", CS_BACHELORS) == 75.0


# ---- regression: bugs in the old implementation --------------------------

def test_literature_is_not_mistaken_for_it():
    """The old code matched the substring "it" inside "Literature"."""

    result = score("Bachelor of Arts in Literature",
                   "Bachelor's degree in Information Technology")

    assert result == 50.0


def test_uppercase_IT_is_recognised_as_information_technology():
    assert score("B.Tech in Information Technology",
                 "Bachelor's degree in IT") == 100.0


def test_masters_degree_is_not_penalised_for_bachelors_requirement():
    """The old code compared levels with == and gave 50."""

    assert score("M.Tech Computer Science", CS_BACHELORS) == 100.0


# ---- several entries, missing data ---------------------------------------

def test_best_entry_wins():
    entries = [
        Education(degree="B.Com"),
        Education(degree="M.Tech", field_of_study="Computer Science"),
    ]

    value, details = evaluate_education(entries, CS_BACHELORS)

    assert value == 100.0
    assert "M.Tech" in details.explanation


def test_no_requirement_scores_full():
    value, details = evaluate_education(
        [Education(degree="B.Tech CSE")], None
    )

    assert value == 100.0
    assert "does not specify" in details.explanation


def test_no_education_on_resume_scores_zero():
    value, details = evaluate_education([], CS_BACHELORS)

    assert value == 0.0
    assert "No education details" in details.explanation


def test_entries_without_text_are_ignored():
    value, _ = evaluate_education([Education()], CS_BACHELORS)

    assert value == 0.0


# ---- explanation ---------------------------------------------------------

def test_explanation_describes_the_outcome():
    _, details = evaluate_education(
        [Education(degree="B.Tech", field_of_study="Computer Science")],
        CS_BACHELORS,
    )

    assert details.required_level == "bachelor's"
    assert details.candidate_level == "bachelor's"
    assert details.required_fields == ["Computer Science"]
    assert details.level_met is True
    assert details.field_relevance == "match"
    assert "meets the requirement" in details.explanation


def test_explanation_flags_a_level_gap():
    _, details = evaluate_education(
        [Education(degree="B.Tech in Computer Science")],
        "Master's in Computer Science",
    )

    assert details.level_met is False
    assert "below the requirement" in details.explanation


# ---- text normalisation --------------------------------------------------

@pytest.mark.parametrize("raw, expected_fragment", [
    ("B.Tech", "btech"),
    ("B.Sc.", "bsc"),
    ("Ph.D", "phd"),
    ("B.E.", "bachelor of engineering"),
    ("Arts & Science", "arts and science"),
])
def test_normalize_text(raw, expected_fragment):
    assert expected_fragment in normalize_text(raw)
