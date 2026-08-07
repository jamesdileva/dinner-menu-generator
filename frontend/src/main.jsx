import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// §13a.3 — apply the user's preferred theme (or default to dark) before first paint.
const root = document.getElementById("root");
const saved = localStorage.getItem("theme");
if (saved === "light" || saved === "dark") {
  root.setAttribute("data-theme", saved);
} else {
  // no preference stored — respect the OS dark-mode flag
  root.setAttribute("data-theme", window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
