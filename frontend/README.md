# Resume Analyzer - Frontend

The web page for Resume Analyzer, built with React and Vite. It sends a resume
and a job description to the backend and shows the match report.

## What you need

- **Node.js 22 (LTS) or newer.** Check with `node -v`. If it's older than 20.19,
  install the LTS version from https://nodejs.org
- The **backend running** (see `../backend/README.md`)

## Run it

Open a terminal in this `frontend` folder, then:

```bash
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

The backend must be running at the same time, in a second terminal:

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

## The status badge

The badge at the top right shows **Server connected** when the backend is
running and **Server offline** when it isn't. If you see "offline", start the
backend (see above). The badge only checks that the server answers; it can't
tell whether your Groq key is valid.

## Settings

By default the page talks to the backend at `http://127.0.0.1:8000`. To change
that, copy `.env.example` to `.env` and edit `VITE_API_URL`, then restart
`npm run dev`.

## Make a production build

```bash
npm run build
```

The finished site is created in the `dist` folder.

## Where things are

| File | What it does |
|---|---|
| `src/App.jsx` | Holds the form values and the loading / result / error state |
| `src/api.js` | Sends the request to the backend and turns errors into messages |
| `src/components/UploadForm.jsx` | Resume drop zone, job fields, checks before sending |
| `src/components/ServerStatus.jsx` | The Server connected / offline badge |
| `src/components/ScoreBreakdown.jsx` | The score and the bar showing how it is made up |
| `src/components/SkillGroups.jsx` | Skills you have, close skills and missing skills (as pills) |
| `src/components/Results.jsx` | The whole report page |
| `src/styles.css` | All colours, fonts and layout (the colours are listed at the top) |
