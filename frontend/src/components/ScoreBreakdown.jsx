import { useEffect, useState } from "react";

import {
  CATEGORIES,
  formatNumber,
  skillSummary,
  tierFor,
  verdictFor,
} from "../format.js";

// Each category owns a slice of the 100 points (its weight). The slice fills
// up as far as the candidate scored in that category, so the filled part of
// the whole bar is the overall score.
export default function ScoreBreakdown({ result }) {
  const [ready, setReady] = useState(false);

  // Fill the bar after the first paint so the change is visible
  useEffect(() => {
    const frame = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  const matching = result.matching_result;
  const overall = matching.overall_score;

  const notes = {
    skill_score: skillSummary(matching.skill_matching),
    project_score: matching.project_matching.relevant_projects.length
      ? `${matching.project_matching.relevant_projects.length} of your projects use skills from this job.`
      : "None of your projects use skills from this job.",
    experience_score:
      result.job_requirements.experience_requirement ||
      "The job doesn't state an experience requirement.",
    education_score:
      result.job_requirements.education_requirement ||
      "The job doesn't state an education requirement.",
  };

  return (
    <section
      className={`card score${ready ? " is-ready" : ""}`}
      aria-labelledby="score-heading"
    >
      <div className="score-number" aria-hidden="true">
        <span className="score-value">{Math.round(overall)}</span>
        <span className="score-outof">out of 100</span>
      </div>

      <div className="score-body">
        <h2 id="score-heading" className={`verdict tier-${tierFor(overall)}`}>
          {verdictFor(overall)}
          <span className="visually-hidden">
            , {formatNumber(overall)} out of 100
          </span>
        </h2>

        <div className="bar" aria-hidden="true">
          {CATEGORIES.map((category, index) => (
            <div
              className="bar-segment"
              key={category.key}
              style={{ flexGrow: category.weight }}
            >
              <div
                className="bar-fill"
                style={{
                  "--fill": `${matching[category.key]}%`,
                  "--seg": `var(--seg-${index + 1})`,
                }}
              />
            </div>
          ))}
        </div>

        <ul className="breakdown">
          {CATEGORIES.map((category, index) => (
            <li className="breakdown-row" key={category.key}>
              <span
                className="swatch"
                style={{ "--seg": `var(--seg-${index + 1})` }}
                aria-hidden="true"
              />

              <div className="breakdown-text">
                <span className="breakdown-label">{category.label}</span>
                <span className="breakdown-note">{notes[category.key]}</span>
              </div>

              <div className="breakdown-figures">
                <span className="breakdown-score">
                  {formatNumber(matching[category.key])}
                  <span className="breakdown-max"> / 100</span>
                </span>
                <span className="breakdown-weight">
                  {category.weight}% of the total
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
