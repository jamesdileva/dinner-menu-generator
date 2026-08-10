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
    setOpen(false);
  };

  const handleTakeout = () => {
    onPickTakeout();
    setOpen(false);
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
          <div className="row-wrap" style={{ gap: "6px", marginBottom: "8px" }}>
            <button className="btn-sm" style={{ flex: 1 }} onClick={handleHome}>
              Home
            </button>
            <button className="btn-sm" style={{ flex: 1 }} onClick={handleTakeout}>
              Takeout
            </button>
          </div>
          {result && (
            <div style={{ fontSize: "13px" }}>
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
