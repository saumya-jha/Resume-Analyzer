# Resume Analyzer 

Resume Analyzer checks how well a resume matches a job description. Upload a resume, paste a job post, and get a match score out of 100, along with the skills you have, the skills you are missing, and what to improve first.

The AI reads the documents. The scoring itself is plain, testable Python, so every score can be explained.

* ✅ Skill matching, with related skills earning partial credit
* 📁 Project relevance
* 💼 Experience and 🎓 education checks

Built using React, FastAPI and the Groq LLM, so anyone can test their resume against any job.

## 🌐 Live Demo

🔗 https://frontend-mu-two-38.vercel.app

Try it out live, no installation needed!

> The backend runs on a free plan and sleeps when nobody is using it. If the first visit is slow, wait up to a minute for it to wake up.

## 📚 Features

* Upload a resume as PDF or DOCX and paste any job description
* Overall match score out of 100, with a breakdown for skills, projects, experience and education
* Skills grouped as **You have**, **Close** (related, counts for half) and **Missing**
* Understands different spellings of the same skill (NodeJS = Node.js) and that some skills imply others (MySQL means SQL)
* Finds which of your projects use skills from the job
* Reads education levels and fields (B.Tech, B.E., BCA and "Bachelor's" are treated as the same level)
* Experience from date ranges, without double-counting overlapping jobs
* Shows what the AI read from your resume and the job post, so you can check it
* Clear error messages for bad files, password-protected PDFs and server problems
* 254 automated tests

## 🛠️ Tech Stack

* Language: Python, JavaScript
* Backend: FastAPI, Pydantic
* Frontend: React, Vite, plain CSS
* AI: Groq (`openai/gpt-oss-120b`)
* File reading: pypdf, python-docx
* Testing: pytest
* Deployment: Render (backend), Vercel (frontend)

## 🧠 How Scoring Works

The AI only **extracts** information from the resume and the job post. The score is then calculated in normal code:

| Part | Weight | What it checks |
|---|---|---|
| Skills | 50% | Required skills found on the resume. Related skills count for half |
| Projects | 25% | How many required skills your projects use |
| Experience | 15% | Years of experience against the requirement |
| Education | 10% | Degree level and field of study |

Because the scoring is plain code, the same extracted data always gives the same score, and each rule can be tested.

## 🚀 How to Run Locally

You need Python 3.12 or newer, Node.js 22 or newer, and a free API key from [console.groq.com](https://console.groq.com).

1. Clone the repository

```
git clone https://github.com/saumya-jha/Resume-Analyzer.git
cd Resume-Analyzer
```

2. Start the backend

```
cd backend
python -m venv venv
venv\Scripts\activate         # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env        # macOS/Linux: cp .env.example .env
```

Open the new `.env` file and paste your key after `GROQ_API_KEY=`. Then run:

```
uvicorn app.main:app --reload
```

3. Start the frontend, in a second terminal

```
cd frontend
npm install
npm run dev
```

4. Visit in your browser

```
http://localhost:5173
```

The API documentation is at `http://127.0.0.1:8000/docs`.

## 🔌 API Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/upload-resume` | Check a PDF/DOCX and return its text |
| POST | `/analyze-resume` | Resume file to structured data |
| POST | `/analyze-job` | Job description to structured requirements |
| POST | `/analyze-match` | Resume file and job details to scores, matches and suggestions |

## 🧪 Tests

```
cd backend
pytest
```

## 🔒 Security and Limits

* Uploads are checked by file content, not only by name, and limited to 5 MB
* Password-protected and very long PDFs are rejected with a clear message
* Resume and job text is passed to the AI as data, with guards against prompt injection
* Errors shown to users never include internal details
* The API key is read from a `.env` file that is never uploaded to GitHub

## 🌱 Future Scope

* 🤖 AI-assisted skill matching for skills outside the built-in list
* 📄 Downloadable PDF report
* 🗂️ Saved history to compare resumes and jobs
* 📎 Job description upload as a file
* 🔁 Same job description always giving the same skill list

## 📄 References

* Groq – https://console.groq.com
* FastAPI – https://fastapi.tiangolo.com
* React – https://react.dev
* Vite – https://vite.dev
