import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// The font is bundled with the app, so nothing is loaded from the internet
import "@fontsource-variable/schibsted-grotesk";

import App from "./App.jsx";
import "./styles.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
