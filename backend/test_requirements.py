from app.schemas.requirements_schema import JobRequirements

requirements = JobRequirements(
    required_skills=["Java",  "SpringBoot", "SQL","REST APIs"],
    experience_requirements = "0-2 years",
    educational_requirements = "B.Tech in Computer Science",
    responsibilities=[
        "Developing APIs",
        "Debugging applications",
        "Working with databases"
    ]
)

print(requirements)
print(requirements.model_dump())