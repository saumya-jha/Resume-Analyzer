// Small helpers for turning the backend's numbers into readable text.

// Order and weights match the backend (backend/app/services/matching_service.py)
export const CATEGORIES = [
  { key: "skill_score", label: "Skills", weight: 50 },
  { key: "project_score", label: "Projects", weight: 25 },
  { key: "experience_score", label: "Experience", weight: 15 },
  { key: "education_score", label: "Education", weight: 10 },
];

export function verdictFor(score) {
  if (score >= 75) return "Strong match";
  if (score >= 50) return "Partial match";
  if (score >= 25) return "Weak match";
  return "Low match";
}

// Used to colour the verdict badge
export function tierFor(score) {
  if (score >= 75) return "strong";
  if (score >= 50) return "partial";
  if (score >= 25) return "weak";
  return "low";
}

export function formatNumber(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function plural(count, singular, pluralForm = `${singular}s`) {
  return `${count} ${count === 1 ? singular : pluralForm}`;
}

// "6 of 17 required skills match, 2 are close."
export function skillSummary(skillMatching) {
  const matched = skillMatching.matched_skills.length;
  const near = skillMatching.partially_matched_skills.length;
  const total = matched + near + skillMatching.missing_skills.length;

  let text = `${matched} of ${total} required skills match`;

  if (near > 0) {
    text += `, and ${near} more ${near === 1 ? "is" : "are"} close`;
  }

  return `${text}.`;
}
