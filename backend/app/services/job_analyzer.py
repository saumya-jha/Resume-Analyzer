from app.services.groq_client import client, MODEL
from app.schemas.requirements_schema import JobRequirements


def analyze_job_description(job_description: str) -> JobRequirements:

    
    prompt = f"""
    You are an expert technical recruiter.
    Carefully analyze the job description below.
    
    Extract the following information:

    1. required_skills:
       Identify every technical skill, programming language,
       framework, database, and relevant technical concept.
       Return them as a list of strings.

    2. experience_requirement:
       Extract the required years of experience.
       If not mentioned, return null.

    3. education_requirement:
       Extract the required educational qualification.
       If not mentioned, return null.

    4. responsibilities:
       Extract the main duties and responsibilities.
       Return them as a list of strings.
       
    Important rules:
    - Read the entire job description before extracting.
    - Do not skip skills mentioned under requirements.
    - Include skills such as Java, Spring Boot, SQL and REST APIs.
    - Do not invent information.
    - If a field is not mentioned, return null for optional fields 
    and an empty list for list fields.
    - Return only valid JSON.
    - Follow this exact structure:
    
    {{
    "required_skills": ["skill1", "skill2"],
    "experience_requirement": "0-2 years",
    "education_requirement": "Bachelor's degree",
    "responsibilities": ["responsibility1", "responsibility2"]
    }}

    Job Description:
    {job_description}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an expert job description analyzer. Return accurate structured information in JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    result = response.choices[0].message.content

    requirements = JobRequirements.model_validate_json(result)

    return requirements