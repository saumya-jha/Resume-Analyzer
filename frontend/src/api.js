// Talks to the FastAPI backend.

export const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

// Keep these in step with the backend (backend/.env.example)
export const MAX_FILE_MB = 5;
export const MIN_DESCRIPTION_CHARS = 50;

export class ApiError extends Error {}

// The backend sends { detail: "text" }. FastAPI's own validation errors send
// { detail: [{ msg: "text" }, ...] }.
function readDetail(body) {
  const detail = body && body.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join(" ");
  }

  return null;
}

export async function analyzeMatch(
  { file, jobTitle, companyName, jobDescription },
  signal
) {
  const form = new FormData();

  form.append("file", file);
  form.append("job_title", jobTitle.trim());
  form.append("job_description", jobDescription.trim());

  if (companyName.trim()) {
    form.append("company_name", companyName.trim());
  }

  let response;

  try {
    response = await fetch(`${API_URL}/analyze-match`, {
      method: "POST",
      body: form,
      signal,
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;

    throw new ApiError(
      `Can't reach the server at ${API_URL}. Check that the backend is running, then try again.`
    );
  }

  let body = null;

  try {
    body = await response.json();
  } catch {
    // The response was not JSON; fall through to the generic message below
  }

  if (!response.ok) {
    throw new ApiError(
      readDetail(body) ||
        `The server returned an error (${response.status}). Try again in a moment.`
    );
  }

  return body;
}
