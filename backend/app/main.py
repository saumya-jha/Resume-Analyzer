from dotenv import load_dotenv
import os
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print("Groq API key loaded:", GROQ_API_KEY is not None)
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title=" Resume Analyzer",
    description="AI-powered Resume and Job Description Analyzer",
    version="1.0.0"
)

app.include_router(router)
