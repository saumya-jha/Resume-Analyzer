"""End-to-end API tests with real PDF / DOCX files and a stubbed AI."""

import pytest

from app.core.errors import LLMRateLimitError
from app.services import resume_upload

RESUME_LINES = [
    "Asha Verma",
    "asha@example.com",
    "Skills: Java, Spring Boot, MySQL",
    "Education: B.Tech Computer Science",
]


def pdf_file(data, name="resume.pdf"):
    return {"file": (name, data, "application/pdf")}


def docx_file(data, name="resume.docx"):
    return {
        "file": (
            name,
            data,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }


# ---- basics --------------------------------------------------------------

def test_home_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "healthy"


def test_cors_allows_the_vite_frontend(client):
    response = client.options(
        "/analyze-match",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_other_websites(client):
    response = client.options(
        "/analyze-match",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_security_header_is_added(client):
    assert client.get("/health").headers["x-content-type-options"] == "nosniff"


# ---- /upload-resume ------------------------------------------------------

def test_upload_pdf_extracts_text(client, make_pdf):
    response = client.post(
        "/upload-resume", files=pdf_file(make_pdf(RESUME_LINES))
    )

    assert response.status_code == 200
    assert "Asha Verma" in response.json()["extracted_text"]
    assert response.json()["filename"] == "resume.pdf"


def test_upload_docx_extracts_paragraphs_and_tables(client, make_docx):
    data = make_docx(
        paragraphs=["Asha Verma"],
        table_rows=[["Skills", "Java, Spring Boot"]],
    )

    response = client.post("/upload-resume", files=docx_file(data))

    text = response.json()["extracted_text"]

    assert response.status_code == 200
    assert "Asha Verma" in text
    assert "Java, Spring Boot" in text


def test_uppercase_extension_is_accepted(client, make_pdf):
    response = client.post(
        "/upload-resume", files=pdf_file(make_pdf(RESUME_LINES), "CV.PDF")
    )

    assert response.status_code == 200


def test_wrong_extension_is_rejected(client):
    response = client.post(
        "/upload-resume",
        files={"file": ("resume.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Only PDF and DOCX" in response.json()["detail"]


def test_file_with_fake_pdf_content_is_rejected(client):
    response = client.post("/upload-resume", files=pdf_file(b"just some text"))

    assert response.status_code == 400
    assert "Invalid PDF" in response.json()["detail"]


def test_zip_that_is_not_a_docx_is_rejected(client):
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("notes.txt", "hello")

    response = client.post("/upload-resume", files=docx_file(buffer.getvalue()))

    assert response.status_code == 400
    assert "Invalid DOCX" in response.json()["detail"]


def test_empty_file_is_rejected(client):
    response = client.post("/upload-resume", files=pdf_file(b""))

    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_oversized_file_is_rejected(client, monkeypatch):
    monkeypatch.setattr(resume_upload.settings, "max_upload_mb", 1)

    data = b"%PDF-" + b"0" * (2 * 1024 * 1024)

    response = client.post("/upload-resume", files=pdf_file(data))

    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


def test_pdf_without_text_gives_a_helpful_message(client, make_pdf):
    response = client.post("/upload-resume", files=pdf_file(make_pdf([])))

    assert response.status_code == 400
    assert "No readable text" in response.json()["detail"]


def test_password_protected_pdf_is_rejected(client, make_pdf):
    data = make_pdf(RESUME_LINES, password="secret")

    response = client.post("/upload-resume", files=pdf_file(data))

    assert response.status_code == 400
    assert "password" in response.json()["detail"].lower()


def test_pdf_with_too_many_pages_is_rejected(client, make_pdf, monkeypatch):
    monkeypatch.setattr(
        "app.services.resume_parser.settings.max_pdf_pages", 2
    )

    response = client.post(
        "/upload-resume", files=pdf_file(make_pdf(RESUME_LINES, pages=3))
    )

    assert response.status_code == 400
    assert "too many pages" in response.json()["detail"]


def test_corrupted_pdf_does_not_crash(client):
    data = b"%PDF-1.4 this is not really a pdf"

    response = client.post("/upload-resume", files=pdf_file(data))

    assert response.status_code == 400
    assert "Unable to read" in response.json()["detail"]


def test_folder_path_in_filename_is_removed(client, make_pdf):
    response = client.post(
        "/upload-resume",
        files=pdf_file(make_pdf(RESUME_LINES), "../../etc/my resume.pdf"),
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "my resume.pdf"


def test_missing_file_is_a_validation_error(client):
    assert client.post("/upload-resume").status_code == 422


# ---- /analyze-resume and /analyze-job -------------------------------------

def test_analyze_resume(client, make_pdf, stub_ai):
    response = client.post(
        "/analyze-resume", files=pdf_file(make_pdf(RESUME_LINES))
    )

    assert response.status_code == 200
    assert response.json()["resume"]["candidate_name"] == "Asha Verma"


def test_analyze_job(client, stub_ai, job_description):
    response = client.post(
        "/analyze-job",
        json={"job_title": "Backend Developer", "job_description": job_description},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["requirements"]["required_skills"][0] == "Java"
    assert body["company_name"] is None


def test_analyze_job_rejects_short_description(client, stub_ai):
    response = client.post(
        "/analyze-job",
        json={"job_title": "Dev", "job_description": "too short"},
    )

    assert response.status_code == 422


# ---- /analyze-match ------------------------------------------------------

def match_form(job_description, **overrides):
    form = {
        "job_title": "Backend Developer",
        "job_description": job_description,
    }
    form.update(overrides)

    return form


def test_full_matching_workflow_with_pdf(client, make_pdf, stub_ai, job_description):
    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form(job_description, company_name="Acme"),
    )

    body = response.json()

    assert response.status_code == 200
    assert body["candidate_name"] == "Asha Verma"
    assert body["company_name"] == "Acme"
    assert body["matching_result"]["overall_score"] >= 85
    assert "education_matching" in body["matching_result"]
    assert body["resume"]["technical_skills"]
    assert body["job_requirements"]["required_skills"]


def test_full_matching_workflow_with_docx(client, make_docx, stub_ai, job_description):
    response = client.post(
        "/analyze-match",
        files=docx_file(make_docx(RESUME_LINES)),
        data=match_form(job_description),
    )

    assert response.status_code == 200


def test_company_name_is_optional(client, make_pdf, stub_ai, job_description):
    """Used to crash with a 500 error when the field was left out."""

    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form(job_description),
    )

    assert response.status_code == 200
    assert response.json()["company_name"] is None


def test_blank_company_name_is_accepted(client, make_pdf, stub_ai, job_description):
    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form(job_description, company_name=""),
    )

    assert response.status_code == 200


def test_short_job_description_gives_422_with_a_readable_message(
    client, make_pdf, stub_ai
):
    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form("too short"),
    )

    assert response.status_code == 422
    assert "job_description" in response.json()["detail"]


def test_invalid_resume_is_rejected_before_any_ai_call(
    client, monkeypatch, job_description
):
    def must_not_be_called(text):
        raise AssertionError("AI should not be called for an invalid file")

    monkeypatch.setattr("app.api.routes.analyze_resume", must_not_be_called)
    monkeypatch.setattr(
        "app.api.routes.analyze_job_description", must_not_be_called
    )

    response = client.post(
        "/analyze-match",
        files=pdf_file(b"not a pdf"),
        data=match_form(job_description),
    )

    assert response.status_code == 400


def test_job_with_no_skills_gives_a_clear_error(
    client, make_pdf, monkeypatch, strong_resume, job_description
):
    from app.schemas.requirements_schema import JobRequirements

    monkeypatch.setattr(
        "app.api.routes.analyze_resume", lambda text: strong_resume
    )
    monkeypatch.setattr(
        "app.api.routes.analyze_job_description",
        lambda text: JobRequirements(),
    )

    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form(job_description),
    )

    assert response.status_code == 422
    assert "No skills" in response.json()["detail"]


# ---- error handling ------------------------------------------------------

def test_ai_rate_limit_becomes_429_with_friendly_message(
    client, make_pdf, monkeypatch, backend_job, job_description
):
    def busy(text):
        raise LLMRateLimitError()

    monkeypatch.setattr("app.api.routes.analyze_resume", busy)
    monkeypatch.setattr(
        "app.api.routes.analyze_job_description", lambda text: backend_job
    )

    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form(job_description),
    )

    assert response.status_code == 429
    assert "busy" in response.json()["detail"]


def test_unexpected_errors_do_not_leak_details(
    client, make_pdf, monkeypatch, backend_job, job_description
):
    def broken(text):
        raise RuntimeError("secret internal detail: api_key=abc123")

    monkeypatch.setattr("app.api.routes.analyze_resume", broken)
    monkeypatch.setattr(
        "app.api.routes.analyze_job_description", lambda text: backend_job
    )

    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form(job_description),
    )

    assert response.status_code == 500
    assert "secret" not in response.text
    assert "abc123" not in response.text


def test_both_ai_calls_run_in_parallel(
    client, make_pdf, monkeypatch, strong_resume, backend_job, job_description
):
    """analyze-resume and analyze-job are independent, so they must overlap."""

    import threading
    import time

    started = []
    both_started = threading.Event()

    def slow(result):
        def call(text):
            started.append(time.monotonic())

            if len(started) == 2:
                both_started.set()

            # Fails (times out) if the other call never starts alongside us
            assert both_started.wait(timeout=3), "AI calls ran one after another"

            return result

        return call

    monkeypatch.setattr("app.api.routes.analyze_resume", slow(strong_resume))
    monkeypatch.setattr(
        "app.api.routes.analyze_job_description", slow(backend_job)
    )

    response = client.post(
        "/analyze-match",
        files=pdf_file(make_pdf(RESUME_LINES)),
        data=match_form(job_description),
    )

    assert response.status_code == 200
