import pytest
from pydantic import ValidationError

from app.schemas.job_schema import JobDescription

DESCRIPTION = "x" * 60


def make(**overrides):
    values = {
        "job_title": "Backend Developer",
        "company_name": "Acme",
        "job_description": DESCRIPTION,
    }
    values.update(overrides)

    return JobDescription(**values)


def test_valid_job_is_accepted():
    job = make()

    assert job.job_title == "Backend Developer"
    assert job.company_name == "Acme"


def test_company_name_is_optional():
    """/analyze-match passes company_name=None when the field is left out.
    The old validator crashed with AttributeError on None."""

    assert make(company_name=None).company_name is None

    assert JobDescription(
        job_title="Dev", job_description=DESCRIPTION
    ).company_name is None


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_company_name_becomes_none(blank):
    assert make(company_name=blank).company_name is None


def test_values_are_trimmed():
    job = make(job_title="  Dev  ", company_name="  Acme  ")

    assert job.job_title == "Dev"
    assert job.company_name == "Acme"


@pytest.mark.parametrize("field, value", [
    ("job_title", ""),
    ("job_title", "   "),
    ("job_title", "A"),
    ("job_title", "x" * 201),
    ("job_description", "too short"),
    ("job_description", " " * 80),
    ("job_description", "x" * 20001),
    ("company_name", "x" * 201),
])
def test_invalid_values_are_rejected(field, value):
    with pytest.raises(ValidationError):
        make(**{field: value})


def test_job_title_and_description_are_required():
    with pytest.raises(ValidationError):
        JobDescription(job_title="Dev")

    with pytest.raises(ValidationError):
        JobDescription(job_description=DESCRIPTION)
