"""Skill normalisation and matching.

A required skill is compared with a candidate in this order:

1. FULL credit  - the candidate lists it (under any common spelling), or a
                  listed skill implies it (MySQL -> SQL, Spring Boot -> Java),
                  or it is clearly mentioned in their projects / experience.
2. PARTIAL credit - the candidate has a closely related skill (Django when
                  Flask is required, Java when Spring Boot is required).
3. Otherwise the skill is missing.

All the knowledge lives in the plain dictionaries below, so adding a new
alias or relationship is a one-line change.
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache

from app.schemas.matching_schema import SkillMatching

FULL = "full"
PARTIAL = "partial"


# --------------------------------------------------------------------------
# Knowledge base
# --------------------------------------------------------------------------

# canonical name -> other common spellings
_ALIAS_GROUPS = {
    # languages
    "javascript": ["js", "java script", "ecmascript", "es6", "es2015"],
    "typescript": ["ts"],
    "python": ["py", "python3", "python 3"],
    "java": ["core java", "java se"],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp"],
    ".net": ["dotnet", "dot net", ".net core", "asp.net", "asp.net core"],
    "golang": ["go", "go lang"],
    # web
    "node.js": ["node", "nodejs", "node js"],
    "react": ["react.js", "reactjs", "react js"],
    "react native": ["reactnative"],
    "angular": ["angularjs", "angular.js", "angular js"],
    "vue": ["vue.js", "vuejs", "vue js"],
    "next.js": ["nextjs", "next js"],
    "express": ["express.js", "expressjs", "express js"],
    "jquery": ["j query"],
    "spring boot": ["springboot", "spring-boot", "spring boot framework"],
    "spring": ["spring framework", "spring mvc"],
    "html": ["html5", "html 5"],
    "css": ["css3", "css 3"],
    "tailwind css": ["tailwind", "tailwindcss"],
    # databases
    "sql": ["structured query language"],
    "mysql": ["my sql"],
    "postgresql": ["postgres", "postgre sql", "postgres sql", "psql"],
    "sql server": [
        "mssql", "ms sql", "ms sql server", "microsoft sql server",
        "sqlserver",
    ],
    "pl/sql": ["plsql", "pl sql"],
    "mongodb": ["mongo", "mongo db"],
    "nosql": [
        "no sql", "no-sql", "nosql databases", "nosql database",
        "non-relational databases", "non relational databases",
    ],
    "databases": [
        "database", "dbms", "database management",
        "database management systems",
    ],
    "relational databases": [
        "relational database", "relational db", "rdbms", "sql databases",
        "sql database", "relational data stores",
    ],
    # data / ML
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "artificial intelligence": ["ai"],
    "natural language processing": ["nlp"],
    "llm": [
        "llms", "large language model", "large language models",
        "llm development", "llm applications", "generative ai", "genai",
        "gen ai",
    ],
    "ai coding tools": [
        "ai coding agents", "ai coding assistants", "ai coding tool",
        "ai assistants", "ai code assistants", "cursor", "claude code",
        "github copilot", "copilot", "codex", "windsurf",
    ],
    "gemini": ["gemini ai", "google gemini", "gemini api"],
    "openai": ["openai api", "chatgpt", "gpt", "gpt-4", "gpt-4o"],
    "rag": ["retrieval augmented generation", "retrieval-augmented generation"],
    "hugging face": ["huggingface"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "tensorflow": ["tf"],
    "pytorch": ["torch"],
    "power bi": ["powerbi"],
    # cloud / devops
    "aws": ["amazon web services", "amazon aws"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "cloud computing": ["cloud", "cloud platforms", "cloud services"],
    "kubernetes": ["k8s"],
    "ci/cd": [
        "cicd", "ci cd", "ci-cd", "continuous integration",
        "continuous deployment", "continuous delivery",
    ],
    "github actions": ["github action"],
    "gitlab ci": ["gitlab-ci", "gitlab ci/cd"],
    # concepts
    "rest apis": [
        "rest api", "rest", "restful api", "restful apis", "restful",
        "restful web services", "rest services", "restful services",
        "web apis",
    ],
    "microservices": ["micro services", "microservice"],
    "apis": [
        "api", "api development", "api integration", "api integrations",
        "web api",
    ],
    "data structures and algorithms": [
        "dsa", "data structures", "algorithms", "data structures & algorithms",
    ],
    "object oriented programming": [
        "oop", "oops", "object-oriented programming", "object oriented",
    ],
    "agile": ["agile methodology", "agile methodologies"],
}

# Having the key skill means the candidate also has these (full credit).
IMPLIES = {
    # Java world
    "spring boot": {"java", "spring"},
    "spring": {"java"},
    "hibernate": {"java", "orm"},
    "jpa": {"java", "orm"},
    "junit": {"java"},
    # Python world
    "django": {"python"},
    "flask": {"python", "apis"},
    "fastapi": {"python", "apis"},
    "pandas": {"python"},
    "numpy": {"python"},
    "pytest": {"python"},
    "sqlalchemy": {"python", "orm"},
    "scikit-learn": {"python", "machine learning"},
    # JavaScript world
    "react": {"javascript"},
    "angular": {"javascript"},
    "vue": {"javascript"},
    "jquery": {"javascript"},
    "node.js": {"javascript"},
    "express": {"node.js", "javascript", "apis"},
    "next.js": {"react", "javascript"},
    "react native": {"react", "javascript"},
    "typescript": {"javascript"},
    # ML
    "deep learning": {"machine learning"},
    "tensorflow": {"machine learning", "deep learning"},
    "pytorch": {"machine learning", "deep learning"},
    "keras": {"machine learning", "deep learning"},
    "natural language processing": {"machine learning"},
    # databases
    "mysql": {"sql", "relational databases", "databases"},
    "postgresql": {"sql", "relational databases", "databases"},
    "sqlite": {"sql", "relational databases", "databases"},
    "oracle": {"sql", "relational databases", "databases"},
    "sql server": {"sql", "relational databases", "databases"},
    "mariadb": {"sql", "relational databases", "databases"},
    "pl/sql": {"sql", "relational databases", "databases"},
    "sql": {"relational databases", "databases"},
    "relational databases": {"databases"},
    "mongodb": {"nosql", "databases"},
    "cassandra": {"nosql", "databases"},
    "dynamodb": {"nosql", "databases"},
    "redis": {"nosql", "databases"},
    "nosql": {"databases"},
    # APIs
    "graphql": {"apis"},
    "rest apis": {"apis"},
    "postman": {"apis"},
    "swagger": {"apis"},
    # LLMs
    "openai": {"llm"},
    "gemini": {"llm"},
    "langchain": {"llm"},
    "llamaindex": {"llm"},
    "groq": {"llm"},
    "ollama": {"llm"},
    "rag": {"llm"},
    "hugging face": {"machine learning"},
    # hosting platforms
    "vercel": {"cloud computing"},
    "netlify": {"cloud computing"},
    "heroku": {"cloud computing"},
    "firebase": {"cloud computing"},
    # cloud / devops
    "aws": {"cloud computing"},
    "azure": {"cloud computing"},
    "gcp": {"cloud computing"},
    "ec2": {"aws"},
    "s3": {"aws"},
    "lambda": {"aws"},
    "eks": {"aws", "kubernetes"},
    "aks": {"azure", "kubernetes"},
    "gke": {"gcp", "kubernetes"},
    "jenkins": {"ci/cd"},
    "github actions": {"ci/cd", "git"},
    "gitlab ci": {"ci/cd", "git"},
    "github": {"git"},
    "gitlab": {"git"},
    "bitbucket": {"git"},
}

# Required skill -> candidate skills that earn PARTIAL credit.
RELATED_TO = {
    "spring boot": {"java", "spring"},
    "spring": {"java"},
    "django": {"python"},
    "flask": {"python"},
    "fastapi": {"python"},
    "pyramid": {"python"},
    "react": {"javascript"},
    "angular": {"javascript", "typescript"},
    "vue": {"javascript"},
    "node.js": {"javascript"},
    "next.js": {"react"},
    "typescript": {"javascript"},
    "llm": {"machine learning", "natural language processing"},
    "orm": {"sqlalchemy", "hibernate", "jpa"},
    "rest apis": {
        "fastapi", "flask", "django", "express", "spring boot", "node.js",
    },
    "mysql": {"sql"},
    "postgresql": {"sql"},
    "oracle": {"sql"},
    "sql server": {"sql"},
    "kubernetes": {"docker"},
    "machine learning": {"data science", "artificial intelligence"},
}

# Skills in the same group earn PARTIAL credit for one another.
RELATED_GROUPS = [
    {"aws", "azure", "gcp"},
    {"aws", "azure", "gcp", "vercel", "heroku", "netlify", "firebase",
     "render", "digitalocean"},
    {"django", "flask", "fastapi"},
    {"react", "angular", "vue"},
    {"mysql", "postgresql", "sql server", "oracle", "sqlite", "mariadb"},
    {"mongodb", "cassandra", "dynamodb"},
    {"tensorflow", "pytorch", "keras"},
    {"jenkins", "github actions", "gitlab ci", "circleci"},
    {"selenium", "cypress", "playwright"},
]

# These are ordinary English words, or too short to trust when scanning free
# text (project descriptions), so they only count when listed as a skill.
TEXT_STOPLIST = {
    "rest", "next", "express", "spark", "swift", "rust", "go", "spring",
    "excel", "r", "c", "bootstrap", "algorithms", "torch",
    "ml", "ai", "dl", "ts", "js", "py",
}

# Any skill phrase containing these words is the same skill
PATTERN_ALIASES = [
    (re.compile(r"\b(?:llms?|large language models?)\b"), "llm"),
]

# Skills written with a slash that must NOT be split into two skills
KEEP_TOGETHER = {"ci/cd", "tcp/ip", "ui/ux", "pl/sql", "a/b testing", "i/o"}


# --------------------------------------------------------------------------
# Lookup tables built from the knowledge base
# --------------------------------------------------------------------------

def _nospace(text: str) -> str:
    return re.sub(r"[\s\-_.]", "", text)


ALIASES: dict[str, str] = {}
_NOSPACE_ALIASES: dict[str, str] = {}
SURFACE_FORMS: dict[str, set[str]] = {}

for _canonical, _variants in _ALIAS_GROUPS.items():
    _forms = {_canonical, *_variants}
    SURFACE_FORMS[_canonical] = _forms
    for _form in _forms:
        ALIASES[_form] = _canonical
        _NOSPACE_ALIASES.setdefault(_nospace(_form), _canonical)

# Every skill the knowledge base knows about. Used to spot skills that are
# only mentioned in free text ("built the API with MySQL").
KNOWN_SKILLS: set[str] = (
    set(SURFACE_FORMS)
    | set(IMPLIES)
    | set(RELATED_TO)
    | {skill for skills in IMPLIES.values() for skill in skills}
    | {skill for skills in RELATED_TO.values() for skill in skills}
    | {skill for group in RELATED_GROUPS for skill in group}
)


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

def normalize_skill(skill: str) -> str:
    """Return the canonical lower-case name of a skill.

    "NodeJS", "node" and "Node.js" all become "node.js";
    "Postgres SQL" becomes "postgresql"; "Spring-Boot" becomes "spring boot".
    """

    text = (skill or "").lower()
    text = re.sub(r"\([^)]*\)", " ", text)  # drop notes such as "(Java)"
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip(" \t,;:|*•·-_/\"'")
    text = text.rstrip(".")

    if text in ALIASES:
        return ALIASES[text]

    nospace = _nospace(text)

    if nospace in _NOSPACE_ALIASES:
        return _NOSPACE_ALIASES[nospace]

    # The AI words the same skill differently from run to run
    # ("LLM-based system development", "LLM fine-tuning", ...)
    for pattern, canonical in PATTERN_ALIASES:
        if pattern.search(text):
            return canonical

    return text


def split_compound(skill: str) -> list[str]:
    """Split "HTML/CSS" into ["HTML", "CSS"], but keep "CI/CD" together."""

    cleaned = re.sub(r"\([^)]*\)", " ", skill or "").strip()

    if "/" not in cleaned or normalize_skill(cleaned) in KEEP_TOGETHER:
        return [cleaned]

    parts = [part.strip() for part in cleaned.split("/") if part.strip()]

    return parts or [cleaned]


def expand_listed_skills(raw_skills) -> set[str]:
    """Turn the skills a candidate lists into a set of canonical skills.

    Handles combined entries such as "Python, Java", "HTML/CSS" and
    "Python (Flask, Django)".
    """

    skills: set[str] = set()

    for raw in raw_skills or []:

        if not raw:
            continue

        inside_brackets = re.findall(r"\(([^)]*)\)", raw)
        main_text = re.sub(r"\([^)]*\)", " ", raw)

        pieces = re.split(r"[,;|•]", main_text)

        for chunk in inside_brackets:
            pieces += re.split(r"[,;|/&]| and ", chunk)

        for piece in pieces:

            whole = normalize_skill(piece)

            if whole:
                skills.add(whole)

            for part in split_compound(piece):

                normalized = normalize_skill(part)

                if normalized:
                    skills.add(normalized)

    return skills


def with_implied_skills(skills: set[str]) -> set[str]:
    """Add everything the given skills imply (MySQL -> SQL -> databases)."""

    result = set(skills)
    pending = list(skills)

    while pending:

        current = pending.pop()

        for implied in IMPLIES.get(current, ()):

            if implied not in result:
                result.add(implied)
                pending.append(implied)

    return result


# --------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------

@dataclass
class CandidateProfile:
    """What we know a candidate can do, plus free text as supporting proof."""

    skills: set[str] = field(default_factory=set)
    text: str = ""


@lru_cache(maxsize=2048)
def _form_regex(form: str):
    return re.compile(
        r"(?<![\w+#.])" + re.escape(form) + r"(?![\w+#])",
        re.IGNORECASE,
    )


def _mentioned_in_text(skill: str, text: str) -> bool:
    """Whole-word search, so "java" never matches inside "javascript"."""

    if not text:
        return False

    for form in SURFACE_FORMS.get(skill, {skill}):

        if len(form) < 3 or form in TEXT_STOPLIST:
            continue

        if _form_regex(form).search(text):
            return True

    return False


def build_candidate_profile(listed_skills, evidence_text: str = "") -> CandidateProfile:
    """Combine listed skills with skills proven by free text.

    A mention such as "built the backend with MySQL" counts like a listed
    skill, so it also implies SQL.
    """

    text = (evidence_text or "").lower()

    skills = expand_listed_skills(listed_skills)

    if text:
        skills |= {
            skill for skill in KNOWN_SKILLS if _mentioned_in_text(skill, text)
        }

    return CandidateProfile(skills=with_implied_skills(skills), text=text)


def _match_single(term: str, profile: CandidateProfile) -> str | None:

    skill = normalize_skill(term)

    if not skill:
        return None

    if skill in profile.skills or _mentioned_in_text(skill, profile.text):
        return FULL

    if RELATED_TO.get(skill, set()) & profile.skills:
        return PARTIAL

    for group in RELATED_GROUPS:
        if skill in group and (group - {skill}) & profile.skills:
            return PARTIAL

    return None


def match_skill(required_skill: str, profile: CandidateProfile) -> str | None:
    """Return FULL, PARTIAL or None for one required skill.

    "AWS or Azure or GCP" is a choice: having any one of them is enough.
    """

    alternatives = [
        option.strip()
        for option in re.split(r"\s+or\s+", required_skill or "", flags=re.IGNORECASE)
        if option.strip()
    ]

    if len(alternatives) > 1:

        outcomes = [match_skill(option, profile) for option in alternatives]

        if FULL in outcomes:
            return FULL

        return PARTIAL if PARTIAL in outcomes else None

    results = [
        _match_single(part, profile)
        for part in split_compound(required_skill)
    ]

    if all(result == FULL for result in results):
        return FULL

    if all(result is None for result in results):
        return None

    return PARTIAL


def unique_required_skills(required_skills) -> list[str]:
    """Remove duplicates such as "Java" / "java" / "Core Java"."""

    seen = set()
    unique = []

    for skill in required_skills or []:

        key = normalize_skill(skill)

        if key and key not in seen:
            seen.add(key)
            unique.append(skill)

    return unique


def match_skills(
    resume_skills,
    required_skills,
    evidence_text: str = "",
) -> SkillMatching:
    """Sort every required skill into matched / partial / missing.

    resume_skills: skills the candidate lists (including project technologies)
    evidence_text: project descriptions, responsibilities etc. that can prove
                   a skill the candidate forgot to list
    """

    profile = build_candidate_profile(resume_skills, evidence_text)

    matched, partially_matched, missing = [], [], []

    for skill in unique_required_skills(required_skills):

        result = match_skill(skill, profile)

        if result == FULL:
            matched.append(skill)
        elif result == PARTIAL:
            partially_matched.append(skill)
        else:
            missing.append(skill)

    return SkillMatching(
        matched_skills=matched,
        partially_matched_skills=partially_matched,
        missing_skills=missing,
    )


def calculate_percentage(matched, total) -> float:

    if total == 0:
        return 100.0

    return round((matched / total) * 100, 2)


def calculate_skill_score(skill_matching: SkillMatching, total_required=None) -> float:
    """Full match = 1 point, partial match = 0.5 point.

    The total is derived from the matching result itself (duplicates were
    already removed), so total_required is only kept for compatibility.
    """

    total = (
        len(skill_matching.matched_skills)
        + len(skill_matching.partially_matched_skills)
        + len(skill_matching.missing_skills)
    )

    weighted = (
        len(skill_matching.matched_skills)
        + 0.5 * len(skill_matching.partially_matched_skills)
    )

    return calculate_percentage(weighted, total)
