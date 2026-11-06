from app.services.resume_analyzer import analyze_resume


resume_text = """
Samya Jha
Email: samya@example.com
Phone: 9876543210

EDUCATION
B.Tech in Computer Science
JNTUH
Graduation Year: 2026

TECHNICAL SKILLS
Python, Java, C, SQL, Flask, FastAPI, React

PROJECTS

SmartHarvest
Developed an ML-based web application for farmers.
Implemented crop recommendation and yield prediction.
Technologies: Python, Flask, Machine Learning.

PrajaGov
Developed a civic grievance management platform.
Implemented issue classification using Gemini AI.
Technologies: React, FastAPI, PostgreSQL, Gemini AI.

EXPERIENCE
No professional work experience.

CERTIFICATIONS
No certifications mentioned.
"""

resume = analyze_resume(resume_text)

print("\nExtracted Resume Information:\n")
print(resume.model_dump())