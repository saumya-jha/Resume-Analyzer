# Resume Analyzer - Backend

FastAPI backend that reads a resume (PDF / DOCX), reads a job description, and
scores how well they match. The AI (Groq) only **extracts** structured data;
the scoring itself is plain, testable Python.

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
# then open .env and paste your GROQ_API_KEY
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API page.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/upload-resume` | Validate a PDF/DOCX and return its text |
| POST | `/analyze-resume` | Resume file -> structured data |
| POST | `/analyze-job` | Job description JSON -> requirements |
| POST | `/analyze-match` | Resume file + job form fields -> scores, matches, suggestions |

`/analyze-match` is form-data: `file`, `job_title`, `job_description`,
and optional `company_name`.

## How scoring works

Overall = skills 50% + projects 25% + experience 15% + education 10%.

* **Skills** (`services/skill_matching.py`) - spellings are normalised
  (NodeJS = Node.js), specific skills imply general ones (MySQL -> SQL),
  related skills earn half credit (Flask for Django), and skills proven only in
  project/experience text still count. To teach it a new skill, edit the
  dictionaries at the top of that file.
* **Projects** - how many required skills your projects demonstrate.
* **Experience** (`services/matching_service.py`) - date ranges are parsed and
  merged (overlapping jobs are not double-counted).
* **Education** (`services/education_matching.py`) - B.Tech, B.E., B.Sc, BCA and
  "Bachelor's" are the same level; a higher degree satisfies a lower
  requirement; related fields get full or partial credit.

## Configuration (`.env`)

See `.env.example`. Upload size, PDF page limit, AI timeout and the allowed
frontend origins (CORS) are all configurable.

## Tests

```bash
pytest
```

The tests never call the real AI, so they are free and need no API key.
