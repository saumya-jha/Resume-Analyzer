import { useEffect, useRef, useState } from "react";

import { analyzeMatch, ApiError } from "./api.js";
import { DocumentIcon, SparkleIcon } from "./components/icons.jsx";
import Results from "./components/Results.jsx";
import ServerStatus from "./components/ServerStatus.jsx";
import UploadForm from "./components/UploadForm.jsx";

// The AI can take a while; stop waiting after this long
const TIMEOUT_MS = 120_000;

export default function App() {
  const [values, setValues] = useState({
    file: null,
    jobTitle: "",
    companyName: "",
    jobDescription: "",
  });
  const [status, setStatus] = useState("idle"); // idle | loading | done
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const controllerRef = useRef(null);
  const cancelledRef = useRef(false);
  const errorRef = useRef(null);

  // Bring a new error into view, so it isn't missed below the form
  useEffect(() => {
    if (!error) return;

    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    errorRef.current?.scrollIntoView({
      block: "center",
      behavior: calm ? "auto" : "smooth",
    });
  }, [error]);

  function updateValues(changes) {
    setValues((current) => ({ ...current, ...changes }));
  }

  async function handleSubmit() {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    controllerRef.current = controller;
    cancelledRef.current = false;

    setError(null);
    setStatus("loading");

    try {
      const data = await analyzeMatch(values, controller.signal);

      setResult(data);
      setStatus("done");
    } catch (caught) {
      setStatus("idle");

      if (caught.name === "AbortError") {
        // A person pressing Cancel needs no message
        if (!cancelledRef.current) {
          setError(
            "This is taking too long. Try again in a moment, or use a shorter job description."
          );
        }
      } else if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Something went wrong. Try again.");
      }
    } finally {
      clearTimeout(timer);
    }
  }

  function handleCancel() {
    cancelledRef.current = true;
    controllerRef.current?.abort();
  }

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-mark">
              <DocumentIcon size={26} />
            </span>
            <div className="brand-text">
              <span className="brand-name">Resume Analyzer</span>
              <span className="brand-tag">Intelligent resume evaluation</span>
            </div>
          </div>

          <ServerStatus />
        </div>
      </header>

      <main className="shell">
        {status === "done" && result ? (
          <Results result={result} onBack={() => setStatus("idle")} />
        ) : (
          <>
            <section className="hero">
              <p className="hero-badge">
                <SparkleIcon />
                AI-powered resume analysis
              </p>

              <h1 className="hero-title">
                Check your resume against any job
                <span className="hero-accent">in seconds.</span>
              </h1>

              <p className="hero-text">
                Upload your resume and paste a job description. The AI compares
                skills, experience, education and projects, then shows what
                matches, what's missing, and what to improve first.
              </p>
            </section>

            <UploadForm
              values={values}
              onChange={updateValues}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              loading={status === "loading"}
            />

            <div className="status" aria-live="polite">
              {status === "loading" && (
                <p className="status-text">
                  Reading your resume and the job post. This usually takes 10 to
                  20 seconds.
                </p>
              )}
            </div>

            {error && (
              <div className="error" role="alert" ref={errorRef}>
                <p className="error-title">The analysis didn't finish</p>
                <p>{error}</p>
              </div>
            )}
          </>
        )}
      </main>
    </>
  );
}
