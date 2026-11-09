"""Education scoring.

Compares the candidate's degrees with a job's education requirement.

How it works
------------
* Every education entry is scored on its own, and the best entry wins
  (so an M.Tech in CS plus an older diploma is judged by the M.Tech).
* Score of one entry = 50% degree level + 50% field of study.
* Degree level: B.Tech, B.E., B.Sc., BCA, "Bachelor's" ... are all the same
  level (bachelor). A higher level than required counts as fully met.
  One level below the requirement earns half credit.
* Field of study: matched on whole words only (so "Literature" can never be
  mistaken for "IT"). Same field = full credit, a closely related computing
  field = full credit, a neighbouring STEM field = partial credit.
"""

import re

from app.schemas.matching_schema import EducationMatching
from app.schemas.resume_schema import Education


# --------------------------------------------------------------------------
# Degree levels
# --------------------------------------------------------------------------

LEVEL_LABELS = {
    0: "school",
    1: "diploma",
    2: "bachelor's",
    3: "master's",
    4: "PhD",
}

# (rank, regex) -- applied to normalised text (lower case, no dots)
LEVEL_PATTERNS = [
    (4, r"\b(phd|ph d|doctorate|doctoral|doctor of philosophy|dphil)\b"),
    (3, r"\b(masters?|postgraduate|post graduate|m ?tech|m ?sc|ms|mca|mba|"
        r"m ?com|mphil|m ?eng)\b"),
    (2, r"\b(bachelors?|undergraduate|b ?tech|b ?sc|bs|b ?eng|bca|bba|"
        r"b ?com|ba)\b"),
    (1, r"\b(diploma|polytechnic|associates?)\b"),
    (0, r"\b(high school|higher secondary|secondary|hsc|ssc|12th|10th|xii|"
        r"intermediate)\b"),
]

# A requirement that just says "a degree" means a bachelor's degree
GENERIC_DEGREE_PATTERN = r"\b(degree|graduate|graduation)\b"


# --------------------------------------------------------------------------
# Fields of study
# --------------------------------------------------------------------------

# name -> (family, regex). Longer phrases come first inside each regex.
FIELD_PATTERNS = {
    "computer_science": (
        "computing",
        r"\b(computer science (and )?engineering|computer science|cse|cs|"
        r"computer engineering|computer systems|computer technology|"
        r"computing)\b",
    ),
    "information_technology": (
        "computing",
        r"\b(information technology|information science|"
        r"information systems|infotech)\b",
    ),
    "software_engineering": (
        "computing",
        r"\b(software engineering|software development|software systems)\b",
    ),
    "computer_applications": (
        "computing",
        r"\b(computer applications?|bca|mca)\b",
    ),
    "data_science": (
        "computing",
        r"\b(data science|data analytics|artificial intelligence|"
        r"machine learning|ai ?ml|ai ?ds|ai and (ml|ds)|aiml|aids)\b",
    ),
    "cybersecurity": (
        "computing",
        r"\b(cyber ?security|information security|network security)\b",
    ),
    "electronics": (
        "electrical",
        r"\b(electronics (and communications?)?|electrical( and electronics)?|"
        r"ece|eee|instrumentation|telecommunications?)\b",
    ),
    "mathematics": (
        "science",
        r"\b(mathematics|maths|math|statistics|physics|applied science)\b",
    ),
    "mechanical_civil_other": (
        "engineering_other",
        r"\b(mechanical|civil|chemical|aerospace|automobile|production|"
        r"industrial engineering|biotechnology)\b",
    ),
    "business": (
        "business",
        r"\b(business|mba|bba|commerce|b ?com|m ?com|management|finance|"
        r"accounting|economics)\b",
    ),
    "humanities": (
        "humanities",
        r"\b(arts|literature|english|history|humanities|psychology|"
        r"sociology|law|journalism|political)\b",
    ),
}

STEM_FAMILIES = {"computing", "electrical", "science", "engineering_other"}

# A degree that is clearly engineering but names no branch (plain "B.Tech")
ENGINEERING_DEGREE_PATTERN = r"\b(b ?tech|m ?tech|b ?eng|m ?eng|engineering)\b"

# Requirement wording that accepts any engineering / technical discipline
BROAD_STEM_PATTERN = (
    r"\b(any|other|relevant|related)\s+(engineering|technical|technology|"
    r"stem|scientific)\b|\bengineering (discipline|field|stream|branch)\b|"
    r"\bstem\b"
)

# Requirement wording that tolerates a neighbouring field
LENIENT_PATTERN = r"\b(related|relevant|similar|allied|equivalent)\b"

FIELD_FAMILY = {name: family for name, (family, _) in FIELD_PATTERNS.items()}
FIELD_FAMILY["engineering_generic"] = "engineering_other"
FIELD_FAMILY["any_stem"] = "stem_any"


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Lower-case text and expand abbreviations that are ambiguous words.

    "B.E." / "BE" and "IT" are normal English words when lower-cased, so they
    are expanded here, while the original capitalisation is still available.
    """

    if not text:
        return ""

    text = re.sub(
        r"\bB\.\s?E\b", " bachelor of engineering ", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\bBE\b", " bachelor of engineering ", text)
    text = re.sub(
        r"\bM\.\s?E\b", " master of engineering ", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\bIT\b", " information technology ", text)

    text = text.lower().replace("&", " and ")
    text = text.replace(".", "")
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    return re.sub(r"\s+", " ", text).strip()


def detect_levels(text: str) -> set[int]:
    """Return every degree level mentioned in already-normalised text."""

    return {
        rank
        for rank, pattern in LEVEL_PATTERNS
        if re.search(pattern, text)
    }


def detect_fields(text: str) -> set[str]:
    """Return the fields of study mentioned in already-normalised text."""

    return {
        name
        for name, (_, pattern) in FIELD_PATTERNS.items()
        if re.search(pattern, text)
    }


def _field_label(name: str) -> str:
    return {"any_stem": "any engineering / technical field"}.get(
        name, name.replace("_", " ").title()
    )


# --------------------------------------------------------------------------
# Requirement parsing
# --------------------------------------------------------------------------

def parse_requirement(requirement: str) -> tuple[int | None, set[str], bool]:
    """Return (minimum level rank, accepted fields, lenient about field)."""

    text = normalize_text(requirement)

    levels = detect_levels(text)

    if levels:
        # "Bachelor's or Master's" -> a bachelor's is enough
        required_level = min(levels)
    elif re.search(GENERIC_DEGREE_PATTERN, text):
        required_level = 2
    else:
        required_level = None

    fields = detect_fields(text)

    if re.search(BROAD_STEM_PATTERN, text):
        fields.add("any_stem")

    if not fields and re.search(r"\b(engineering|technology)\b", text):
        fields.add("any_stem")

    lenient = bool(re.search(LENIENT_PATTERN, text))

    return required_level, fields, lenient


# --------------------------------------------------------------------------
# Scoring pieces
# --------------------------------------------------------------------------

def score_level(required: int | None, candidate: int | None):
    """Return (score between 0 and 1, level_met)."""

    if required is None:
        return 1.0, True

    if candidate is None:
        return 0.5, None

    if candidate >= required:
        return 1.0, True

    if candidate == required - 1:
        return 0.5, False

    return 0.0, False


def score_field(required: set[str], candidate: set[str], lenient: bool):
    """Return (score between 0 and 1, relevance label)."""

    if not required:
        return 1.0, "not_required"

    if not candidate:
        return 0.5, "unknown"

    if required & candidate:
        return 1.0, "match"

    required_families = {FIELD_FAMILY[field] for field in required}
    candidate_families = {FIELD_FAMILY[field] for field in candidate}

    if "stem_any" in required_families:
        if candidate_families & STEM_FAMILIES:
            return 1.0, "match"
        return 0.0, "unrelated"

    if required_families & candidate_families:
        return 1.0, "related"

    if (
        required_families & STEM_FAMILIES
        and candidate_families & STEM_FAMILIES
    ):
        return (0.75 if lenient else 0.5), "adjacent"

    return 0.0, "unrelated"


def _entry_text(entry: Education) -> str:
    return " ".join(
        part for part in (entry.degree, entry.field_of_study) if part
    ).strip()


def _candidate_fields(raw_text: str) -> set[str]:
    text = normalize_text(raw_text)

    fields = detect_fields(text)

    if not fields and re.search(ENGINEERING_DEGREE_PATTERN, text):
        fields.add("engineering_generic")

    return fields


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def evaluate_education(
    education: list[Education],
    requirement: str | None,
) -> tuple[float, EducationMatching]:
    """Score the candidate's education against the job requirement (0-100)."""

    if not requirement or not requirement.strip():
        return 100.0, EducationMatching(
            explanation="The job does not specify an education requirement."
        )

    required_level, required_fields, lenient = parse_requirement(requirement)

    required_level_label = (
        LEVEL_LABELS[required_level] if required_level is not None else None
    )
    required_field_labels = sorted(
        _field_label(field) for field in required_fields
    )

    entries = [entry for entry in education if _entry_text(entry)]

    if not entries:
        return 0.0, EducationMatching(
            required_level=required_level_label,
            required_fields=required_field_labels,
            explanation="No education details were found on the resume.",
        )

    best = None

    for entry in entries:
        text = _entry_text(entry)
        levels = detect_levels(normalize_text(text))
        candidate_level = max(levels) if levels else None
        candidate_fields = _candidate_fields(text)

        level_score, level_met = score_level(required_level, candidate_level)
        field_score, relevance = score_field(
            required_fields, candidate_fields, lenient
        )

        entry_score = round(100 * (0.5 * level_score + 0.5 * field_score), 2)

        # Highest score wins; on a tie prefer the higher degree level
        ranking = (entry_score, candidate_level if candidate_level is not None else -1)

        if best is None or ranking > best["ranking"]:
            best = {
                "ranking": ranking,
                "score": entry_score,
                "text": text,
                "candidate_level": candidate_level,
                "candidate_fields": candidate_fields,
                "level_met": level_met,
                "relevance": relevance,
            }

    # ---- Build a readable explanation ----
    parts = []

    needs = []
    if required_level_label:
        needs.append(f"a {required_level_label} degree")
    if required_field_labels:
        needs.append("in " + " / ".join(required_field_labels))
    if needs:
        parts.append("The job asks for " + " ".join(needs) + ".")

    candidate_label = (
        LEVEL_LABELS[best["candidate_level"]]
        if best["candidate_level"] is not None
        else None
    )

    parts.append(
        f"Best matching qualification: {best['text']}"
        + (f" ({candidate_label} level)." if candidate_label else ".")
    )

    level_sentence = {
        True: "The degree level meets the requirement.",
        False: "The degree level is below the requirement.",
        None: "The degree level could not be determined from the resume.",
    }[best["level_met"]]

    field_sentence = {
        "match": "The field of study matches.",
        "related": "The field of study is closely related.",
        "adjacent": "The field of study is in a neighbouring discipline "
                    "(partial credit).",
        "unrelated": "The field of study does not match.",
        "unknown": "The field of study is not stated on the resume.",
        "not_required": "",
    }[best["relevance"]]

    parts.extend(sentence for sentence in (level_sentence, field_sentence) if sentence)

    details = EducationMatching(
        required_level=required_level_label,
        candidate_level=candidate_label,
        required_fields=required_field_labels,
        candidate_fields=sorted(
            _field_label(field) for field in best["candidate_fields"]
        ),
        level_met=best["level_met"],
        field_relevance=best["relevance"],
        explanation=" ".join(parts),
    )

    return best["score"], details
