from app.schemas.resume_schema import ResumeData
from app.schemas.requirements_schema import JobRequirements
from app.services.matching_service import match_resume_with_job


# Sample resume data
resume = ResumeData(
    candidate_name="Alex",
    technical_skills=[
        "Java",
        "Python",
        "SQL",
        "React"
    ],
    projects=[
        {
            "project_name": "Student Management System",
            "description": "Developed a backend application",
            "technologies": ["Java","SQL"]
        },
        {
            "project_name": "Weather App",
            "description": "A weather forecasting application",
            "technologies": ["Python", "Flask"]
        }
    ],
    education=[
        {
            "degree": "B.Tech Computer Science",
            "institution": "ABC University",
            "graduation_year": "2026"
        }
    ]
)


# Sample job requirements
job = JobRequirements(
    required_skills=[
        "Java",
        "Spring Boot",
        "SQL",
        "AWS"
    ],
    experience_requirement="0-2 years",
    education_requirement="Bachelor's degree in Computer Science",
    responsibilities=[
        "Develop backend applications",
        "Build REST APIs"
    ]
)


# Run the matching engine
result = match_resume_with_job(resume, job)

print("\n===== RESUME MATCHING RESULT =====")

print(result.model_dump_json(indent=4))