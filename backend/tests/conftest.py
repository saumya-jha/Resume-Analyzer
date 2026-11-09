"""Shared test fixtures.

None of these tests call the real Groq API: the AI layer is replaced by
stubs, so the tests are fast, free and work without an API key.
"""

import io

import pytest
from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app
from app.schemas.requirements_schema import JobRequirements
from app.schemas.resume_schema import Education, Experience, Project, ResumeData


# --------------------------------------------------------------------------
# API client
# --------------------------------------------------------------------------

@pytest.fixture
def client():
    # raise_server_exceptions=False lets us check the 500 response that a
    # real user would receive, instead of the test crashing.
    return TestClient(app, raise_server_exceptions=False)


# --------------------------------------------------------------------------
# Sample data
# --------------------------------------------------------------------------

@pytest.fixture
def strong_resume():
    return ResumeData(
        candidate_name="Asha Verma",
        email="asha@example.com",
        technical_skills=["Java", "Spring Boot", "MySQL", "Git", "Docker"],
        education=[
            Education(
                degree="B.Tech",
                field_of_study="Computer Science",
                institution="ABC University",
                graduation_year="2024",
            )
        ],
        experience=[
            Experience(
                job_title="Backend Developer",
                company="TechCorp",
                duration="Jan 2023 - Jan 2025",
                responsibilities=["Built REST APIs with Spring Boot"],
            )
        ],
        projects=[
            Project(
                project_name="Student Management System",
                description="Backend application with REST APIs",
                technologies=["Java", "Spring Boot", "MySQL"],
            )
        ],
    )


@pytest.fixture
def backend_job():
    return JobRequirements(
        required_skills=["Java", "Spring Boot", "SQL", "REST APIs"],
        experience_requirement="1-3 years",
        education_requirement="Bachelor's degree in Computer Science",
        responsibilities=["Develop backend services"],
    )


JOB_DESCRIPTION = (
    "We are hiring a Backend Developer. Requirements: Java, Spring Boot, "
    "SQL and REST APIs. 1-3 years of experience. Bachelor's degree in "
    "Computer Science."
)


@pytest.fixture
def job_description():
    return JOB_DESCRIPTION


# --------------------------------------------------------------------------
# Real PDF / DOCX files
# --------------------------------------------------------------------------

@pytest.fixture
def make_pdf():

    def build(lines=None, pages=1, password=None):

        buffer = io.BytesIO()

        options = {"encrypt": password} if password else {}

        pdf = canvas.Canvas(buffer, **options)

        for _ in range(pages):
            y = 800

            for line in lines or []:
                pdf.drawString(50, y, line)
                y -= 20

            pdf.showPage()

        pdf.save()

        return buffer.getvalue()

    return build


@pytest.fixture
def make_docx():

    def build(paragraphs=None, table_rows=None):

        document = Document()

        for paragraph in paragraphs or []:
            document.add_paragraph(paragraph)

        if table_rows:
            table = document.add_table(
                rows=len(table_rows), cols=len(table_rows[0])
            )

            for row_index, row in enumerate(table_rows):
                for column_index, value in enumerate(row):
                    table.cell(row_index, column_index).text = value

        buffer = io.BytesIO()
        document.save(buffer)

        return buffer.getvalue()

    return build


# --------------------------------------------------------------------------
# AI stubs
# --------------------------------------------------------------------------

@pytest.fixture
def stub_ai(monkeypatch, strong_resume, backend_job):
    """Replace both AI calls with instant, fixed answers."""

    monkeypatch.setattr(
        "app.api.routes.analyze_resume", lambda text: strong_resume
    )
    monkeypatch.setattr(
        "app.api.routes.analyze_job_description", lambda text: backend_job
    )
