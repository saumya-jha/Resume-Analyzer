
from app.services.matching_service import calculate_education_score
from app.models.resume import Resume, Education


def test_education(requirement, degree):
    resume = Resume(
        education=[
            Education(degree=degree)
        ]
    )

    score = calculate_education_score(resume, requirement)

    print(
        f"Requirement: {requirement}\n"
        f"Candidate: {degree}\n"
        f"Score: {score}\n"
    )


test_cases = [
    ("Bachelor's in Computer Science", "B.Tech in Computer Science"),
    ("Bachelor's in Computer Science", "B.E. in CSE"),
    ("Bachelor's in Computer Science", "B.Sc. in Computer Science"),
    ("Bachelor's in Computer Science", "B.Tech in Information Technology"),
    ("Master's in Computer Science", "B.Tech in Computer Science"),
    ("Bachelor's in Computer Science", "BBA"),
    ("Master's in Computer Science", "MBA"),
]

for requirement, degree in test_cases:
    test_education(requirement, degree)
