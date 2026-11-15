import { useEffect, useState } from "react";

import { API_URL } from "../api.js";

const LABELS = {
  checking: "Checking server",
  online: "Server connected",
  offline: "Server offline",
};

// Asks the backend's /health address whether it is running.
// This only checks that the server is reachable, not that the AI key works.
export default function ServerStatus() {
  const [state, setState] = useState("checking");

  useEffect(() => {
    let active = true;

    async function check() {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 4000);

      try {
        const response = await fetch(`${API_URL}/health`, {
          signal: controller.signal,
        });

        if (active) setState(response.ok ? "online" : "offline");
      } catch {
        if (active) setState("offline");
      } finally {
        clearTimeout(timer);
      }
    }

    check();

    const interval = setInterval(check, 15000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <p
      className={`server server-${state}`}
      role="status"
      title={state === "offline" ? `Can't reach ${API_URL}` : undefined}
    >
      <span className="server-dot" aria-hidden="true" />
      {LABELS[state]}
    </p>
  );
}
