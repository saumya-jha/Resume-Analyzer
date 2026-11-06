from datetime import date

from app.schemas.resume_schema import Experience
from app.services.matching_service import get_total_experience_months


test_cases = [
    ("2 years", 24),
    ("6 months", 6),
    ("1.5 years", 18),
    ("2022 - 2024", 24),
]

for duration, expected in test_cases:
    experience = Experience(duration=duration)

    result = get_total_experience_months([experience])

    print(f"{duration}: {result} months")

    assert result == expected, (
        f"Expected {expected}, but got {result}"
    )


# Test a date range ending in Present
experience = Experience(duration="Jan 2025 - Present")

result = get_total_experience_months([experience])

today = date.today()
expected = (today.year - 2025) * 12 + today.month - 1

print(f"Jan 2025 - Present: {result} months")

assert result == expected

print("\nAll experience tests passed!")