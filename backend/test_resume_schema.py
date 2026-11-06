from app.schemas.resume_schema import ResumeData

resume = ResumeData(
    candidate_name="Samya Jha",
    email="samya@example.com",
    phone="9876543210",

    technical_skills=["Python", "Java", "SQL", "Flask"],

    education=[
        {
            "degree": "B.Tech Computer Science",
            "institution": "JNTUH",
            "graduation_year": "2026"
        }
    ],

    experience=[],

    projects=[
        {
            "project_name": "SmartHarvest",
            "description": "ML-based crop recommendation application",
            "technologies": ["Python", "Flask", "Machine Learning"]
        }
    ],

    certifications=[]
)

print(resume.model_dump())