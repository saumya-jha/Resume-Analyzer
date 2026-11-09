from datetime import date

import pytest

from app.schemas.resume_schema import Experience, ResumeData
from app.services.matching_service import (
    calculate_experience_score,
    format_months,
    get_total_experience_months,
    parse_experience_date,
    parse_required_years,
)


def months(*durations):
    return get_total_experience_months(
        [Experience(duration=duration) for duration in durations]
    )


def resume_with(*durations):
    return ResumeData(
        experience=[Experience(duration=duration) for duration in durations]
    )


# ---- reading dates -------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("Jan 2024", date(2024, 1, 1)),
    ("January 2024", date(2024, 1, 1)),
    ("October 2023", date(2023, 10, 1)),
    ("Sept 2023", date(2023, 9, 1)),
    ("01/2024", date(2024, 1, 1)),
    ("2024-03", date(2024, 3, 1)),
    ("2024", date(2024, 1, 1)),
    ("  mar, 2022 ", date(2022, 3, 1)),
])
def test_parse_experience_date(text, expected):
    assert parse_experience_date(text) == expected


@pytest.mark.parametrize("text", ["Present", "current", "Till date", "ongoing"])
def test_present_means_today(text):
    assert parse_experience_date(text) == date.today()


@pytest.mark.parametrize("text", ["", "soon", "13/2024", "Foo 2024", None])
def test_unreadable_dates_return_none(text):
    assert parse_experience_date(text) is None


# ---- total experience ----------------------------------------------------

@pytest.mark.parametrize("duration, expected", [
    ("2 years", 24),
    ("6 months", 6),
    ("1.5 years", 18),
    ("2 years 3 months", 27),
    ("2022 - 2024", 24),
    ("Jan 2023 - Mar 2023", 2),
    ("June 2022 to August 2022", 2),
    ("2023-01 - 2023-07", 6),
    ("01/2023 - 07/2023", 6),
])
def test_total_months(duration, expected):
    assert months(duration) == expected


@pytest.mark.parametrize("duration, expected", [
    # These all failed in the old code: "to" inside "October" / "Sept"
    ("October 2023 - March 2024", 5),
    ("Sept 2023 - Dec 2023", 3),
    ("October 2023 to December 2023", 2),
])
def test_months_that_contain_to_or_are_abbreviated_differently(duration, expected):
    assert months(duration) == expected


def test_present_end_date():
    today = date.today()

    assert months("Jan 2025 - Present") == (
        (today.year - 2025) * 12 + today.month - 1
    )


def test_overlapping_jobs_are_not_counted_twice():
    # Jan-Jun and Mar-Aug overlap, together Jan-Aug = 7 months
    assert months("Jan 2023 - Jun 2023", "Mar 2023 - Aug 2023") == 7


def test_separate_jobs_are_added():
    assert months("Jan 2022 - Jan 2023", "Jan 2024 - Jul 2024") == 18


def test_missing_or_unreadable_duration_counts_as_zero():
    assert months(None, "", "a while") == 0


def test_end_before_start_is_ignored():
    assert months("Mar 2024 - Jan 2024") == 0


# ---- reading the requirement ---------------------------------------------

@pytest.mark.parametrize("requirement, expected", [
    ("0-2 years", 0.0),
    ("2-4 years", 2.0),
    ("1 to 3 years", 1.0),
    ("3+ years", 3.0),
    ("at least 5 years of experience", 5.0),
    ("3 years of experience in Java", 3.0),
    ("6 months", 0.5),
    ("Freshers", 0.0),
    ("Entry level", 0.0),
    ("Prior backend experience", None),
])
def test_parse_required_years(requirement, expected):
    assert parse_required_years(requirement) == expected


# ---- score ---------------------------------------------------------------

def test_no_requirement_scores_full():
    assert calculate_experience_score(resume_with(), None) == 100.0


def test_fresher_role_scores_full_without_experience():
    assert calculate_experience_score(resume_with(), "Freshers") == 100.0
    assert calculate_experience_score(resume_with(), "0-2 years") == 100.0


def test_meeting_the_requirement_scores_full():
    assert calculate_experience_score(resume_with("3 years"), "3+ years") == 100.0
    assert calculate_experience_score(resume_with("5 years"), "3+ years") == 100.0


def test_partial_experience_scores_proportionally():
    assert calculate_experience_score(resume_with("1 year"), "2 years") == 50.0


def test_plain_number_requirement_is_enforced():
    """The old code treated "3 years of experience" as met by any job."""

    score = calculate_experience_score(
        resume_with("6 months"), "3 years of experience in Java"
    )

    assert score == 16.67


def test_no_experience_scores_zero_when_years_required():
    assert calculate_experience_score(resume_with(), "2+ years") == 0.0


def test_requirement_without_a_number_needs_some_experience():
    assert calculate_experience_score(
        resume_with("6 months"), "Prior backend experience"
    ) == 100.0
    assert calculate_experience_score(
        resume_with(), "Prior backend experience"
    ) == 0.0


# ---- formatting ----------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    (0, "0 months"),
    (1, "1 month"),
    (14, "1 year 2 months"),
    (24, "2 years"),
])
def test_format_months(value, expected):
    assert format_months(value) == expected


# ---- "less than N years" is a cap, not a minimum --------------------------

@pytest.mark.parametrize("requirement", [
    "Less than 4 years of professional experience, internships included.",
    "Up to 2 years",
    "Fewer than 3 years",
    "No more than 5 years of experience",
    "3 years or less",
    "Maximum 2 years",
])
def test_a_cap_is_met_by_a_fresher(requirement):
    assert calculate_experience_score(resume_with(), requirement) == 100.0


@pytest.mark.parametrize("requirement", [
    "At least 2 years",
    "Minimum 3 years, up to 6 years",
    "2-4 years",
    "3+ years",
    "More than 2 years",
])
def test_real_minimums_are_still_enforced(requirement):
    assert calculate_experience_score(resume_with(), requirement) == 0.0


def test_suggestion_has_no_stray_punctuation():
    from app.schemas.matching_schema import SkillMatching
    from app.services.matching_service import generate_suggestions

    text = " ".join(generate_suggestions(
        SkillMatching(),
        experience_score=50.0,
        experience_requirement="3 years of experience.",
        candidate_months=6,
    ))

    assert "3 years of experience;" in text
    assert ".;" not in text
