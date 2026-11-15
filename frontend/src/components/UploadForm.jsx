import { useState } from "react";

import { MAX_FILE_MB, MIN_DESCRIPTION_CHARS } from "../api.js";
import { formatFileSize } from "../format.js";
import { DocumentIcon, UploadIcon } from "./icons.jsx";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx"];

// Returns a message when the file can't be used, otherwise null
export function checkFile(file) {
  if (!file) return "Choose your resume to continue.";

  const name = file.name.toLowerCase();

  if (!ACCEPTED_EXTENSIONS.some((extension) => name.endsWith(extension))) {
    return "This file type isn't supported. Upload a PDF or DOCX file.";
  }

  if (file.size > MAX_FILE_MB * 1024 * 1024) {
    return `This file is ${formatFileSize(file.size)}. The limit is ${MAX_FILE_MB} MB.`;
  }

  if (file.size === 0) return "This file is empty.";

  return null;
}

export default function UploadForm({ values, onChange, onSubmit, loading, onCancel }) {
  const [dragging, setDragging] = useState(false);
  const [showErrors, setShowErrors] = useState(false);

  const { file, jobTitle, companyName, jobDescription } = values;

  const errors = {
    file: checkFile(file),
    jobTitle: jobTitle.trim().length < 2 ? "Enter the job title." : null,
    jobDescription:
      jobDescription.trim().length < MIN_DESCRIPTION_CHARS
        ? `Paste the full job description. It needs at least ${MIN_DESCRIPTION_CHARS} characters.`
        : null,
  };

  const hasErrors = Boolean(
    errors.file || errors.jobTitle || errors.jobDescription
  );

  function handleSubmit(event) {
    event.preventDefault();

    if (loading) return;

    if (hasErrors) {
      setShowErrors(true);
      return;
    }

    onSubmit();
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);

    const dropped = event.dataTransfer.files?.[0];

    if (dropped) onChange({ file: dropped });
  }

  const characters = jobDescription.trim().length;

  return (
    <form className="workspace" onSubmit={handleSubmit} noValidate>
      <div className="workspace-head">
        <p className="eyebrow">Analysis workspace</p>
        <h2 className="workspace-title">Add your resume and the job</h2>
        <p className="workspace-lead">
          Upload your resume and paste the job description. The AI compares both
          and explains how well they match.
        </p>
      </div>

      <div className="form-grid">
        <section className="column" aria-labelledby="resume-heading">
          <div className="column-head">
            <div>
              <h3 id="resume-heading" className="column-label">
                Resume
              </h3>
              <p className="column-sub">Upload your resume</p>
            </div>
            <span className="pill">PDF / DOCX</span>
          </div>

          <label
            className={`drop${dragging ? " is-dragging" : ""}${file ? " has-file" : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              className="visually-hidden"
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              disabled={loading}
              aria-describedby="file-help file-error"
              onChange={(event) => {
                const chosen = event.target.files?.[0];
                if (chosen) onChange({ file: chosen });
                event.target.value = "";
              }}
            />

            <span className="drop-icon">
              {file ? <DocumentIcon size={28} /> : <UploadIcon size={28} />}
            </span>

            {file ? (
              <>
                <span className="drop-main">{file.name}</span>
                <span className="drop-sub" id="file-help">
                  {formatFileSize(file.size)} ·{" "}
                  <span className="browse">Click to choose a different file</span>
                </span>
              </>
            ) : (
              <>
                <span className="drop-main">Drop your resume here</span>
                <span className="drop-sub">
                  or <span className="browse">click to browse</span>
                </span>
                <span className="drop-hint" id="file-help">
                  PDF or DOCX · Maximum size {MAX_FILE_MB} MB
                </span>
              </>
            )}
          </label>

          <p
            className="field-error"
            id="file-error"
            role={showErrors && errors.file ? "alert" : undefined}
          >
            {showErrors && errors.file}
          </p>
        </section>

        <section className="column" aria-labelledby="job-heading">
          <div className="column-head">
            <div>
              <h3 id="job-heading" className="column-label">
                Job description
              </h3>
              <p className="column-sub">The requirements for the position</p>
            </div>
            <span className="pill">Required</span>
          </div>

          <div className="field">
            <label htmlFor="job-title">Job title</label>
            <input
              id="job-title"
              type="text"
              value={jobTitle}
              maxLength={200}
              disabled={loading}
              placeholder="e.g. Junior Software Engineer"
              aria-invalid={showErrors && Boolean(errors.jobTitle)}
              aria-describedby="job-title-error"
              onChange={(event) => onChange({ jobTitle: event.target.value })}
            />
            <p className="field-error" id="job-title-error">
              {showErrors && errors.jobTitle}
            </p>
          </div>

          <div className="field">
            <label htmlFor="company">
              Company <span className="optional">(optional)</span>
            </label>
            <input
              id="company"
              type="text"
              value={companyName}
              maxLength={200}
              disabled={loading}
              onChange={(event) => onChange({ companyName: event.target.value })}
            />
          </div>

          <div className="field">
            <label htmlFor="job-description">Job description</label>
            <textarea
              id="job-description"
              rows={8}
              value={jobDescription}
              maxLength={20000}
              disabled={loading}
              placeholder="Paste the whole posting, including the requirements section."
              aria-invalid={showErrors && Boolean(errors.jobDescription)}
              aria-describedby="job-description-help job-description-error"
              onChange={(event) =>
                onChange({ jobDescription: event.target.value })
              }
            />
            <p className="field-help" id="job-description-help">
              {characters.toLocaleString()} characters
            </p>
            <p className="field-error" id="job-description-error">
              {showErrors && errors.jobDescription}
            </p>
          </div>
        </section>
      </div>

      <div className="actions">
        <button className="button" type="submit" disabled={loading}>
          {loading ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Analyzing
            </>
          ) : (
            "Analyze resume"
          )}
        </button>

        {loading && (
          <button className="button-quiet" type="button" onClick={onCancel}>
            Cancel
          </button>
        )}

        <p className="actions-note">
          This app doesn't save your resume. Its text is sent to Groq's AI
          service to produce the report.
        </p>
      </div>
    </form>
  );
}
