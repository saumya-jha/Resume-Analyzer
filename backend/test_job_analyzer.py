from app.services.job_analyzer import analyze_job_description


job_description = """
We are looking for a Junior Java Developer.

Requirements:
- Bachelor's degree in Computer Science or related field.
- 0-2 years of experience.
- Strong knowledge of Java and Spring Boot.
- Basic understanding of SQL and databases.
- Knowledge of REST APIs.

Responsibilities:
- Develop and maintain backend applications.
- Build and integrate REST APIs.
- Debug and fix software issues.
- Work with the development team.
"""

requirements = analyze_job_description(job_description)

print("\nExtracted Job Requirements:\n")

print(requirements.model_dump())