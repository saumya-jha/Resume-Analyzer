import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.errors import AppError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Analyzer",
    description="AI-powered Resume and Job Description Analyzer",
    version="1.1.0"
)

# Allow the React frontend (Vite dev server) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def basic_protections(request: Request, call_next):
    """Reject oversized uploads early and add a safety header."""

    content_length = request.headers.get("content-length")

    # Allow a little extra room for the form fields around the file
    limit = settings.max_upload_bytes + 1024 * 1024

    if content_length and content_length.isdigit() and int(content_length) > limit:
        return JSONResponse(
            status_code=413,
            content={
                "detail": f"The upload is too large. Maximum file size is "
                          f"{settings.max_upload_mb} MB."
            },
        )

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@app.exception_handler(AppError)
async def handle_app_error(request: Request, error: AppError):
    """Expected problems: the message is safe to show to the user."""

    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail},
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, error: Exception):
    """Unexpected problems: log everything, tell the user nothing sensitive."""

    logger.exception("Unhandled error on %s %s", request.method, request.url.path)

    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our side. Please try again."},
    )


app.include_router(router)
