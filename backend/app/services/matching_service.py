"""Combines skill, project, experience and education scores into one result."""

import re
from datetime import date

from app.schemas.matching_schema import MatchingResult, ProjectMatching
from app.services.education_matching import evaluate_education
from app.services.skill_matching import (
    FULL,
    PARTIAL,
    build_candidate_profile,
    calculate_percentage,
    calculate_skill_score,
    match_skill,
    match_skills,
    normalize_skill,
    unique_required_skills,
)

# Names re-exported so older imports such as
# `from app.services.matching_service import normalize_skill` keep working.
__all__ = [
    "normalize_skill",
    "match_skills",
    "calculate_skill_score",
    "calculate_percentage",
    "calculate_project_score",
    "calculate_education_score",
    "calculate_experience_score",
    "get_total_experience_months",
    "generate_suggestions",
    "match_resume_with_job",
]

# How much each part counts towards the overall score
WEIGHTS = {
    "skills": 0.50,
    "projects": 0.25,
    "experience": 0.15,
    "education": 0.10,
}


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------

def calculate_project_score(projects, required_skills):
    """Percentage of required skills that the projects demonstrate.

    A skill used in a project (as a technology, or clearly mentioned in its
    description) is worth 1 point; a closely related technology is worth 0.5.
    """

    required = unique_required_skills(required_skills)

    if not required:
        return 100.0, ProjectMatching()

    best_credit = {skill: 0.0 for skill in required}
    relevant_projects = []
    explanations = []

    for project in projects:

        profile = build_candidate_profile(
            project.technologies,
            f"{project.project_name} {project.description or ''}",
        )

        demonstrated = []
        related = []

        for skill in required:

            result = match_skill(skill, profile)

            if result == FULL:
                demonstrated.append(skill)
                best_credit[skill] = 1.0

            elif result == PARTIAL:
                related.append(skill)
                best_credit[skill] = max(best_credit[skill], 0.5)

        if demonstrated or related:

            relevant_projects.append(project.project_name)

            sentence = f"{project.project_name} "

            if demonstrated:
                sentence += f"demonstrates: {', '.join(demonstrated)}."

            if related:
                sentence += (
                    ("" if not demonstrated else " ")
                    + f"Related experience with: {', '.join(related)}."
                )

            explanations.append(sentence)

    score = calculate_percentage(sum(best_credit.values()), len(required))

    return score, ProjectMatching(
        relevant_projects=relevant_projects,
        relevance_explanation=explanations,
    )


# --------------------------------------------------------------------------
# Experience
# --------------------------------------------------------------------------

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

PRESENT_WORDS = {
    "present", "current", "currently", "now", "ongoing", "today",
    "till date", "to date", "date", "till now",
}

# "Jan 2023 - Mar 2024", "June 2022 to August 2022" (spaces required, so the
# "to" inside "October" is never mistaken for a separator) ...
_SPACED_RANGE = re.compile(r"\s+(?:-|–|—|to|until|till)\s+")
# ... and "2022-2024", "01/2023-03/2024"
_TIGHT_RANGE = re.compile(r"\s*(?:-|–|—)\s*")

FRESHER_TERMS = (
    "fresher",
    "freshers",
    "entry-level",
    "entry level",
    "no experience required",
    "no prior experience",
)


def parse_experience_date(value):
    """Turn "Jan 2024", "October 2023", "01/2024", "2024" or "Present" into a date."""

    text = (value or "").strip().lower().strip("().,; ")

    if text in PRESENT_WORDS:
        return date.today()

    try:
        match = re.fullmatch(r"([a-z]{3,9})\.?,?\s*(\d{4})", text)
        if match and match.group(1)[:3] in MONTHS:
            return date(int(match.group(2)), MONTHS[match.group(1)[:3]], 1)

        match = re.fullmatch(r"(\d{1,2})\s*[/.\-]\s*(\d{4})", text)
        if match and 1 <= int(match.group(1)) <= 12:
            return date(int(match.group(2)), int(match.group(1)), 1)

        match = re.fullmatch(r"(\d{4})\s*[/.\-]\s*(\d{1,2})", text)
        if match and 1 <= int(match.group(2)) <= 12:
            return date(int(match.group(1)), int(match.group(2)), 1)

        match = re.fullmatch(r"(\d{4})", text)
        if match:
            return date(int(match.group(1)), 1, 1)

    except ValueError:
        return None

    return None


def _split_date_range(duration: str):

    for pattern in (_SPACED_RANGE, _TIGHT_RANGE):

        parts = pattern.split(duration, maxsplit=1)

        if len(parts) == 2:
            return parts

    return None


def get_total_experience_months(experiences):
    """Total months of experience.

    Date ranges are merged first, so two jobs that overlap (an internship
    during a part-time job) are not counted twice.
    """

    ranges = []
    stated_months = 0

    for experience in experiences:

        duration = (experience.duration or "").strip().lower()

        if not duration:
            continue

        parts = _split_date_range(duration)

        if parts:

            start = parse_experience_date(parts[0])
            end = parse_experience_date(parts[1])

            if start and end and end >= start:
                ranges.append((
                    start.year * 12 + start.month,
                    end.year * 12 + end.month,
                ))
                continue

        # Durations such as "2 years", "6 months", "1.5 years"
        for value, unit in re.findall(
            r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)",
            duration,
        ):
            amount = float(value)

            stated_months += amount * 12 if unit.startswith(("year", "yr")) \
                else amount

    ranges.sort()
    merged = []

    for start, end in ranges:

        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return sum(end - start for start, end in merged) + stated_months


def parse_required_years(requirement: str):
    """Minimum years of experience a job asks for, or None if no number is given."""

    text = requirement.lower()

    if any(term in text for term in FRESHER_TERMS):
        return 0.0

    # "2-4 years", "0 to 2 years" -> the lower number
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*\d+(?:\.\d+)?\s*\+?\s*"
        r"(?:years?|yrs?)",
        text,
    )
    if match:
        return float(match.group(1))

    # "3 years", "5+ years", "at least 3 years"
    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*months?", text)
    if match:
        return float(match.group(1)) / 12

    return None


# "Less than 4 years", "up to 2 years", "3 years or less" state a MAXIMUM
_MAXIMUM_WORDS = re.compile(
    r"\b(?:less than|fewer than|under|up to|at most|no more than|"
    r"maximum(?: of)?|max\.?)\s*\d"
    r"|\d+(?:\.\d+)?\s*(?:years?|yrs?)?\s*(?:or less|or fewer|or under)",
    re.IGNORECASE,
)

_MINIMUM_WORDS = re.compile(
    r"\b(?:at least|minimum|min\.?|(?<!no )more than|over)\b", re.IGNORECASE
)


def is_maximum_only(requirement: str) -> bool:
    """True when the job only caps experience (it does not ask for any)."""

    return bool(
        _MAXIMUM_WORDS.search(requirement)
        and not _MINIMUM_WORDS.search(requirement)
    )


def calculate_experience_score(resume, experience_requirement):

    if not experience_requirement:
        return 100.0

    # A cap such as "less than 4 years" is met by anyone, including freshers
    if is_maximum_only(experience_requirement):
        return 100.0

    minimum_years = parse_required_years(experience_requirement)

    if minimum_years is None:
        # e.g. "Prior backend experience" - no number to compare against
        return 100.0 if resume.experience else 0.0

    if minimum_years == 0:
        return 100.0

    candidate_months = get_total_experience_months(resume.experience)

    score = candidate_months / (minimum_years * 12) * 100

    return round(min(score, 100.0), 2)


def format_months(months: float) -> str:

    whole = int(round(months))

    years, remainder = divmod(whole, 12)

    parts = []

    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")

    if remainder or not parts:
        parts.append(f"{remainder} month{'s' if remainder != 1 else ''}")

    return " ".join(parts)


# --------------------------------------------------------------------------
# Education
# --------------------------------------------------------------------------

def calculate_education_score(resume, education_requirement):
    """Score only (0-100). See education_matching for the full explanation."""

    score, _ = evaluate_education(resume.education, education_requirement)

    return score


# --------------------------------------------------------------------------
# Suggestions
# --------------------------------------------------------------------------

def _short_list(items, limit=8):

    shown = ", ".join(items[:limit])

    if len(items) > limit:
        shown += f" and {len(items) - limit} more"

    return shown


def generate_suggestions(
    skill_matching,
    *,
    project_score=100.0,
    experience_score=100.0,
    education_matching=None,
    experience_requirement=None,
    candidate_months=None,
):

    suggestions = []

    if skill_matching.missing_skills:
        suggestions.append(
            "Missing skills: "
            + _short_list(skill_matching.missing_skills)
            + ". If you already know any of them, add them to your resume; "
            "otherwise build a small project to gain hands-on experience."
        )

    if skill_matching.partially_matched_skills:
        suggestions.append(
            "Turn related experience into direct experience with: "
            + _short_list(skill_matching.partially_matched_skills)
        )

    gaps = (
        skill_matching.missing_skills
        + skill_matching.partially_matched_skills
    )

    if project_score < 60 and gaps:
        suggestions.append(
            "Add or expand a project that uses: " + _short_list(gaps, 4)
        )

    if experience_score < 100 and experience_requirement:
        message = (
            "The role asks for "
            + experience_requirement.strip().rstrip(".;, ")
        )

        if candidate_months is not None:
            message += (
                f"; your resume shows about {format_months(candidate_months)}"
            )

        suggestions.append(
            message + ". Highlight internships, freelance or open-source "
            "work to strengthen this."
        )

    if education_matching is not None:

        if education_matching.level_met is False:
            suggestions.append(
                "The role asks for a "
                f"{education_matching.required_level} degree. Mention "
                "relevant certifications or coursework to offset this."
            )

        elif education_matching.field_relevance in ("adjacent", "unrelated"):
            suggestions.append(
                "Your field of study differs from what the role asks for. "
                "Emphasise relevant coursework, projects or certifications."
            )

    if not suggestions:
        suggestions.append(
            "Continue strengthening your skills through practical projects."
        )

    return suggestions


# --------------------------------------------------------------------------
# Overall match
# --------------------------------------------------------------------------

def _resume_evidence(resume):
    """Return (skills the resume lists, free text that can prove other skills)."""

    listed_skills = list(resume.technical_skills)

    for project in resume.projects:
        listed_skills.extend(project.technologies)

    pieces = []

    for project in resume.projects:
        pieces.extend([project.project_name, project.description or ""])

    for experience in resume.experience:
        pieces.append(experience.job_title or "")
        pieces.extend(experience.responsibilities)

    pieces.extend(resume.certifications)

    return listed_skills, "\n".join(pieces)


def match_resume_with_job(resume, job):

    listed_skills, evidence_text = _resume_evidence(resume)

    skill_matching = match_skills(
        listed_skills,
        job.required_skills,
        evidence_text,
    )

    skill_score = calculate_skill_score(skill_matching)

    project_score, project_matching = calculate_project_score(
        resume.projects,
        job.required_skills,
    )

    experience_score = calculate_experience_score(
        resume,
        job.experience_requirement,
    )

    candidate_months = get_total_experience_months(resume.experience)

    education_score, education_matching = evaluate_education(
        resume.education,
        job.education_requirement,
    )

    overall_score = round(
        skill_score * WEIGHTS["skills"]
        + project_score * WEIGHTS["projects"]
        + experience_score * WEIGHTS["experience"]
        + education_score * WEIGHTS["education"],
        2,
    )

    strengths = []

    if skill_matching.matched_skills:
        strengths.append(
            "Exact skill matches: " + ", ".join(skill_matching.matched_skills)
        )

    if skill_matching.partially_matched_skills:
        strengths.append(
            "Related skills: "
            + ", ".join(skill_matching.partially_matched_skills)
        )

    if project_matching.relevant_projects:
        strengths.append(
            "Relevant projects: "
            + ", ".join(project_matching.relevant_projects)
        )

    if job.experience_requirement and experience_score >= 100:
        strengths.append("Meets the experience requirement.")

    if job.education_requirement and education_score >= 100:
        strengths.append("Meets the education requirement.")

    return MatchingResult(
        overall_score=overall_score,
        skill_score=skill_score,
        project_score=project_score,
        experience_score=experience_score,
        education_score=education_score,
        skill_matching=skill_matching,
        project_matching=project_matching,
        education_matching=education_matching,
        strengths=strengths,
        improvement_suggestions=generate_suggestions(
            skill_matching,
            project_score=project_score,
            experience_score=experience_score,
            education_matching=education_matching,
            experience_requirement=job.experience_requirement,
            candidate_months=candidate_months,
        ),
    )
