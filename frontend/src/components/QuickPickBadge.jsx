// Quick Pick badge button for the header (audit §13.21).
// Compact version of the Quick Pick card — opens a popup with Home/Takeout options.
// The result is shown inline in the popup.

import { useState, useRef, useEffect } from "react";

export default function QuickPickBadge({ onPickHome, onPickTakeout, result }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    if (open) {
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
    }
  }, [open]);

  // close on outside click
  useEffect(() => {
    const onClick = (e) => {
      if (open && ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", onClick);
      return () => document.removeEventListener("mousedown", onClick);
    }
  }, [open]);

  const handleHome = () => {
    onPickHome();
    // Don't close — wait for the async result to arrive, then show it
  };

  const handleTakeout = () => {
    onPickTakeout();
    // Don't close — wait for the async result to arrive, then show it
  };

  return (
    <div ref={ref} style={{ display: "inline-block", position: "relative" }}>
      <button
        className="btn-sm"
        style={{ padding: "4px 10px", fontSize: "13px" }}
        onClick={() => setOpen(!open)}
        title="Quick Pick: home or takeout"
      >
        🎲 Quick Pick
      </button>

      {open && (
        <div
          className="quick-pick-popup"
          style={{
            position: "absolute",
            top: "100%",
            right: 0,
            zIndex: 1000,
            minWidth: "200px",
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "10px",
            boxShadow: "var(--shadow)",
            marginTop: "6px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
            <strong style={{ fontSize: "13px" }}>Quick Pick</strong>
            <button
              className="btn-sm"
              style={{
                background: "transparent",
                border: "none",
                fontSize: "16px",
                lineHeight: 1,
                cursor: "pointer",
                color: "var(--text-muted)",
                padding: "0 4px",
              }}
              onClick={() => setOpen(false)}
              title="Close"
            >
              ×
            </button>
          </div>
          <div className="row-wrap" style={{ gap: "6px", marginBottom: "8px" }}>
            <button className="btn-sm" style={{ flex: 1 }} onClick={handleHome}>
              Home
            </button>
            <button className="btn-sm" style={{ flex: 1 }} onClick={handleTakeout}>
              Takeout
            </button>
          </div>
          {result && (
            <div style={{ fontSize: "13px", marginTop: "6px", padding: "6px", background: "var(--bg-panel)", borderRadius: "6px" }}>
              <strong>{result.mode === "home" ? "At Home:" : "Takeout:"}</strong>
              <div>{result.meal?.name || result.meal}</div>
              {result.meal?.type && <div style={{ opacity: 0.7 }}>{result.meal.type}</div>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
