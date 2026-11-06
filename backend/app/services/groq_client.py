import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Find and load the .env file
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Get the API key
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

# Create the Groq client
client = Groq(api_key=api_key)

# Model we'll use
MODEL = "openai/gpt-oss-120b"