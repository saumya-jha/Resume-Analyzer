import { useEffect, useRef } from "react";

import { plural } from "../format.js";
import { ArrowLeftIcon } from "./icons.jsx";
import ScoreBreakdown from "./ScoreBreakdown.jsx";
import SkillGroups from "./SkillGroups.jsx";

function TextList({ items, good = false }) {
  return (
    <ul className={`notes${good ? " notes-good" : ""}`}>
      {items.map((item) => (
        <li className="prose" key={item}>
          {item}
        </li>
      ))}
    </ul>
  );
}

// Lets the person check what the AI actually understood
function ReadBack({ resume, job }) {
  return (
    <details className="card readback">
      <summary>What we read from your resume and the job post</summary>

      <div className="readback-grid">
        <div>
          <h3>Your resume</h3>

          <dl>
            <dt>Skills</dt>
            <dd>{resume.technical_skills.join(", ") || "None found"}</dd>

            <dt>Experience</dt>
            <dd>
              {resume.experience.length === 0
                ? "No work experience found"
                : resume.experience
                    .map((entry) =>
                      [entry.job_title, entry.company, entry.duration]
                        .filter(Boolean)
                        .join(", ")
                    )
                    .join("; ")}
            </dd>

            <dt>Education</dt>
            <dd>
              {resume.education
                .map((entry) =>
                  [entry.degree, entry.field_of_study, entry.institution]
                    .filter(Boolean)
                    .join(", ")
                )
                .join("; ") || "None found"}
            </dd>

            <dt>Projects</dt>
            <dd>
              {resume.projects.map((project) => project.project_name).join("; ") ||
                "None found"}
            </dd>

            {resume.certifications.length > 0 && (
              <>
                <dt>Certifications</dt>
                <dd>{resume.certifications.join("; ")}</dd>
              </>
            )}
          </dl>
        </div>

        <div>
          <h3>The job post</h3>

          <dl>
            <dt>Required skills</dt>
            <dd>{job.required_skills.join(", ")}</dd>

            <dt>Experience</dt>
            <dd>{job.experience_requirement || "Not stated"}</dd>

            <dt>Education</dt>
            <dd>{job.education_requirement || "Not stated"}</dd>
          </dl>
        </div>
      </div>

      <p className="readback-help">
        If something here is wrong or missing, the report will be off too.
        Check that your resume is a text-based PDF or a DOCX file.
      </p>
    </details>
  );
}

export default function Results({ result, onBack }) {
  const headingRef = useRef(null);

  // Move keyboard and screen reader focus to the report
  useEffect(() => {
    window.scrollTo(0, 0);
    headingRef.current?.focus();
  }, []);

  const matching = result.matching_result;
  const projects = matching.project_matching;

  return (
    <div className="results">
      <button className="button-quiet back" type="button" onClick={onBack}>
        <ArrowLeftIcon />
        Edit inputs
      </button>

      <header className="results-header">
        <h1 className="results-title" tabIndex={-1} ref={headingRef}>
          {result.candidate_name || "Your resume"}
          <span className="results-for">
            {" "}
            for {result.job_title}
            {result.company_name ? ` at ${result.company_name}` : ""}
          </span>
        </h1>
      </header>

      <ScoreBreakdown result={result} />

      <SkillGroups skillMatching={matching.skill_matching} />

      <div className="two-up">
        <section className="card" aria-labelledby="next-heading">
          <h2 id="next-heading" className="section-title">
            What to do next
          </h2>
          <TextList items={matching.improvement_suggestions} />
        </section>

        {matching.strengths.length > 0 && (
          <section className="card" aria-labelledby="working-heading">
            <h2 id="working-heading" className="section-title">
              What's working
            </h2>
            <TextList items={matching.strengths} good />
          </section>
        )}
      </div>

      <section className="card" aria-labelledby="projects-heading">
        <h2 id="projects-heading" className="section-title">
          Projects
        </h2>

        {projects.relevance_explanation.length > 0 ? (
          <>
            <p className="section-lead">
              {plural(projects.relevant_projects.length, "project")} on your
              resume {projects.relevant_projects.length === 1 ? "uses" : "use"}{" "}
              skills from this job.
            </p>
            <TextList items={projects.relevance_explanation} />
          </>
        ) : (
          <p className="prose">
            None of your projects use skills from this job. Add a project that
            does, or list the skills you used in each project.
          </p>
        )}
      </section>

      <section className="card" aria-labelledby="education-heading">
        <h2 id="education-heading" className="section-title">
          Education
        </h2>
        <p className="prose">{matching.education_matching.explanation}</p>
      </section>

      <ReadBack resume={result.resume} job={result.job_requirements} />
    </div>
  );
}
