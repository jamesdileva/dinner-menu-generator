import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import ErrorBoundary from "./components/ErrorBoundary.jsx";

// §13a.3 — apply the user's preferred theme (or default to dark) before first paint.
const rootEl = document.getElementById("root");
const saved = localStorage.getItem("theme");
if (saved === "light" || saved === "dark") {
  rootEl.setAttribute("data-theme", saved);
} else {
  // no preference stored — respect the OS dark-mode flag
  rootEl.setAttribute("data-theme", window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

createRoot(rootEl).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
