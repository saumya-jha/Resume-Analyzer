import re
from datetime import date , datetime
from app.schemas.matching_schema import (
    MatchingResult,
    SkillMatching,
    ProjectMatching
)


# Normalize different names for the same technology
SKILL_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "py": "python",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "react.js": "react",
    "reactjs": "react",
    "node.js": "node.js",
    "rest api": "rest apis",
    "restful api": "rest apis",
    "rest apis": "rest apis",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "mongo": "mongodb",
    "mongodb": "mongodb"
}
RELATED_SKILLS = {
    "spring boot": {"java"},
    "django": {"python"},
    "pyramid": {"python"},
    "orm": {"sqlalchemy", "hibernate"},
    "aws": {"azure", "gcp"},
    "azure": {"aws", "gcp"},
    "gcp": {"aws", "azure"},
    "html5": {"html/css"},
    "rest apis": {"fastapi", "flask"}
}


def normalize_skill(skill: str) -> str:
    cleaned_skill = skill.strip().lower()
    return SKILL_ALIASES.get(cleaned_skill, cleaned_skill)


def match_skills(resume_skills, required_skills):

    resume_normalized = {
        normalize_skill(skill) for skill in resume_skills
    }

    matched = []
    partially_matched = []
    missing = []

    for skill in required_skills:

        normalized = normalize_skill(skill)

        # Exact match
        if normalized in resume_normalized:
            matched.append(skill)

        # Check for related skills
        elif RELATED_SKILLS.get(normalized, set()) & resume_normalized:
            partially_matched.append(skill)

        # No exact or related skill found
        else:
            missing.append(skill)

    return SkillMatching(
        matched_skills=matched,
        partially_matched_skills=partially_matched,
        missing_skills=missing
    )


def calculate_percentage(matched, total):

    if total == 0:
        return 100.0

    return round((matched / total) * 100, 2)


def calculate_skill_score(skill_matching, total_required):

    matched_count = len(skill_matching.matched_skills)

    partial_count = len(
        skill_matching.partially_matched_skills
    )

    weighted_count = matched_count + (partial_count * 0.5)

    return calculate_percentage(
        weighted_count,
        total_required
    )

def calculate_project_score(projects, required_skills):

    if not required_skills:
        return 100.0, ProjectMatching()

    relevant_projects = []
    explanations = []

    normalized_required = {
        normalize_skill(skill): skill
        for skill in required_skills
    }

    demonstrated_skills = set()

    for project in projects:

        project_technologies = {
            normalize_skill(tech)
            for tech in project.technologies
        }

        description = (project.description or "").lower()

        project_matches = []

        for normalized_skill, original_skill in normalized_required.items():

            # Check project technology list
            technology_match = (
                normalized_skill in project_technologies
            )

            # Check description using whole-word matching
            description_match = bool(
                re.search(
                    r"(?<!\w)" + re.escape(normalized_skill) + r"(?!\w)",
                    description
                )
            )

            if technology_match or description_match:

                project_matches.append(original_skill)
                demonstrated_skills.add(normalized_skill)

        if project_matches:

            relevant_projects.append(project.project_name)

            explanations.append(
                f"{project.project_name} demonstrates: "
                f"{', '.join(project_matches)}."
            )

    score = calculate_percentage(
        len(demonstrated_skills),
        len(normalized_required)
    )

    return score, ProjectMatching(
        relevant_projects=relevant_projects,
        relevance_explanation=explanations
    )


def parse_experience_date(value):
    value = value.strip()

    if value.lower() in ["present", "current", "now"]:
        return date.today()

    formats = [
        "%b %Y",    # Jan 2024
        "%B %Y",    # January 2024
        "%m/%Y",    # 01/2024
        "%Y"        # 2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None

def parse_experience_date(value):
    value = value.strip()

    if value.lower() in ["present", "current", "now"]:
        return date.today()

    formats = [
        "%b %Y",    # Jan 2024
        "%B %Y",    # January 2024
        "%m/%Y",    # 01/2024
        "%Y"        # 2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def get_total_experience_months(experiences):

    total_months = 0

    for experience in experiences:

        duration = (experience.duration or "").strip().lower()

        if not duration:
            continue

        # First, try to identify a date range
        date_range = re.search(
            r"(.+?)\s*(?:-|–|—|to)\s*(.+)",
            duration,
            re.IGNORECASE
        )

        if date_range:

            start_date = parse_experience_date(date_range.group(1))
            end_date = parse_experience_date(date_range.group(2))

            if start_date and end_date and end_date >= start_date:

                months = (
                    (end_date.year - start_date.year) * 12
                    + end_date.month - start_date.month
                )

                total_months += months
                continue

        # Otherwise, try numeric durations
        matches = re.findall(
            r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)",
            duration
        )

        for value, unit in matches:

            value = float(value)

            if unit.startswith(("year", "yr")):
                total_months += value * 12
            else:
                total_months += value

    return total_months


def calculate_experience_score(resume, experience_requirement):

    if not experience_requirement:
        return 100.0

    requirement = experience_requirement.lower()

    fresher_terms = [
        "fresher",
        "freshers",
        "entry-level",
        "entry level",
        "no experience required"
    ]

    if any(term in requirement for term in fresher_terms):
        return 100.0

    # Extract minimum required experience
    range_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*years?",
        requirement
    )

    minimum_match = re.search(
        r"(?:at least|minimum of|minimum|required)\s*(\d+(?:\.\d+)?)\s*years?",
        requirement
    )

    plus_match = re.search(
        r"(\d+(?:\.\d+)?)\s*\+\s*years?",
        requirement
    )

    if range_match:
        minimum_years = float(range_match.group(1))

    elif minimum_match:
        minimum_years = float(minimum_match.group(1))

    elif plus_match:
        minimum_years = float(plus_match.group(1))

    else:
        zero_match = re.search(r"\b0\s*years?\b", requirement)

        if zero_match:
            return 100.0

        return 100.0 if resume.experience else 0.0

    if minimum_years == 0:
        return 100.0

    candidate_months = get_total_experience_months(
        resume.experience
    )

    required_months = minimum_years * 12

    score = (candidate_months / required_months) * 100

    return round(min(score, 100.0), 2)



def calculate_education_score(resume, education_requirement):

    if not education_requirement:
        return 100.0

    requirement = education_requirement.lower()

    candidate_education = " ".join(
        (education.degree or "").lower()
        for education in resume.education
    )

    if not candidate_education.strip():
        return 0.0

    # Step 1: Identify degree levels
    degree_levels = {
        "bachelor": [
            "bachelor",
            "b.tech", "btech",
            "b.e.", "b.e",
            "b.sc", "bsc",
            "b.s.", "bs",
            "bca",
            "undergraduate",
            "bachelor of technology",
            "bachelor of engineering",
            "bachelor of science"
        ],

        "master": [
            "master",
            "m.tech", "mtech",
            "m.e.", "m.e",
            "m.sc", "msc",
            "mca",
            "postgraduate",
            "master of technology",
            "master of engineering",
            "master of science"
        ],

        "phd": [
            "phd",
            "ph.d",
            "doctorate",
            "doctoral"
        ]
    }

    def identify_level(text):

        for level, keywords in degree_levels.items():

            if any(keyword in text for keyword in keywords):
                return level

        return None

    required_level = identify_level(requirement)
    candidate_level = identify_level(candidate_education)

    # Step 2: Identify relevant fields
    field_categories = {
        "computer_science": [
            "computer science",
            "computer science and engineering",
            "cse",
            "computer engineering"
        ],

        "information_technology": [
            "information technology",
            "information science",
            "it"
        ],

        "software_engineering": [
            "software engineering",
            "software development"
        ],

        "computer_applications": [
            "computer applications"
        ]
    }

    def identify_field(text):

        for field, keywords in field_categories.items():

            if any(keyword in text for keyword in keywords):
                return field

        return None

    required_field = identify_field(requirement)
    candidate_field = identify_field(candidate_education)

    # Step 3: Compare degree levels
    level_matches = (
        required_level is None
        or candidate_level == required_level
    )

    # Step 4: Compare fields
    if required_field is None:
        field_matches = True

    elif required_field == candidate_field:
        field_matches = True

    elif required_field == "computer_science" and candidate_field in [
        "information_technology",
        "software_engineering"
    ]:
        field_matches = True

    else:
        field_matches = False

    # Step 5: Calculate score
    if level_matches and field_matches:
        return 100.0

    if level_matches or field_matches:
        return 50.0

    return 0.0



def generate_suggestions(skill_matching):

    suggestions = []

    if skill_matching.missing_skills:
        suggestions.append(
            "Consider learning and practicing: "
            + ", ".join(skill_matching.missing_skills)
        )

    if skill_matching.partially_matched_skills:
        suggestions.append(
            "Build practical experience with: "
            + ", ".join(skill_matching.partially_matched_skills)
        )

    if not suggestions:
        suggestions.append(
            "Continue strengthening your skills through practical projects."
        )

    return suggestions


def match_resume_with_job(resume, job):

    skill_matching = match_skills(
        resume.technical_skills,
        job.required_skills
    )

    skill_score = calculate_skill_score(
        skill_matching,
        len(job.required_skills)
    )

    project_score, project_matching = calculate_project_score(
        resume.projects,
        job.required_skills
    )

    experience_score = calculate_experience_score(
        resume,
        job.experience_requirement
    )

    education_score = calculate_education_score(
        resume,
        job.education_requirement
    )

    overall_score = round(
        skill_score * 0.50
        + project_score * 0.25
        + experience_score * 0.15
        + education_score * 0.10,
        2
    )

    strengths = []

    if skill_matching.matched_skills:
        strengths.append(
        "Exact skill matches: "
        + ", ".join(skill_matching.matched_skills)
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

    result = MatchingResult(
        overall_score=overall_score,
        skill_score=skill_score,
        project_score=project_score,
        experience_score=experience_score,
        education_score=education_score,
        skill_matching=skill_matching,
        project_matching=project_matching,
        strengths=strengths,
        improvement_suggestions=generate_suggestions(skill_matching)
    )

    return result