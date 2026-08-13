// Insights tab (audit B2): last-few-weeks macro overview + deficiency flags +
// rule-based swap suggestions. §16.3: when Ollama is enabled and available, the
// backend augments the response with ``ai_suggestions`` (nuanced, meal-specific
// guidance). Lazy-fetches GET /insights (no backend DB writes).

const barWrap = { marginTop: "8px", marginBottom: "6px" };
const barTrack = { flex: 1, height: "12px", background: "var(--bg-panel)", borderRadius: "6px", overflow: "hidden" };

export default function Insights({ data, onGenerate, ollamaEnabled }) {
  if (data === null) {
    return (
      <div className="card">
        <h2>Insights</h2>
        <button className="btn" onClick={onGenerate}>
          Load Insights
        </button>
        <p style={{ opacity: 0.7, marginTop: "8px", fontSize: "13px" }}>
          Macro overview over your last few weekly menus.
        </p>
      </div>
    );
  }

  const totals = data.totals || {};
  const targets = data.weekly_targets || {};
  const weeks = data.weeks_reviewed || 0;

  return (
    <div className="card">
      <h2>Insights</h2>
      <p style={{ opacity: 0.7, fontSize: "13px" }}>
        Reviewing <strong>{weeks}</strong> {weeks === 1 ? "menu" : "menus"} (last {weeks} weeks).
      </p>

      <div style={{ marginTop: "12px" }}>
        {Object.keys(totals).map((macro) => {
          const t = targets[macro] || 0;
          const total = totals[macro] || 0;
          const pct = t ? Math.round((total / t) * 100) : 0;
          return (
            <div key={macro} style={barWrap}>
              <div className="row-between" style={{ fontSize: "13px" }}>
                <span style={{ width: "110px", color: "var(--text-muted)" }}>{macro}</span>
                <span style={{ opacity: 0.8 }}>{total}/{t}</span>
              </div>
              <div style={barTrack}>
                <div
                  style={{
                    height: "100%",
                    width: `${Math.min(pct, 100)}%`,
                    background: pct >= 100 ? "var(--accent)" : "#fbbf24",
                    borderRadius: "6px",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {data.flags && data.flags.length > 0 ? (
        <div style={{ marginTop: "12px" }}>
          <h3 style={{ color: "var(--text-muted)", fontSize: "14px" }}>Needs attention</h3>
          {data.flags.map((f) => (
            <div key={f} style={{ color: "var(--text-warning)", marginBottom: "4px" }}>
              • {f}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ marginTop: "12px", color: "var(--text-success)" }}>
          • Looking balanced
        </div>
      )}

      <div style={{ marginTop: "12px" }}>
        <h3 style={{ color: "var(--text-muted)", fontSize: "14px" }}>Swap suggestions</h3>
        {(data.suggestions || []).map((s, i) => (
          <div key={i} style={{ color: "var(--text-success)", marginBottom: "6px" }}>
            • {s}
          </div>
        ))}
      </div>

      {/* §16.3 — AI-enhanced insights (shown when available) */}
      {ollamaEnabled && data.ai_suggestions && data.ai_suggestions.length > 0 && (
        <div style={{ marginTop: "12px", padding: "10px", background: "var(--bg-panel)", borderRadius: "8px" }}>
          <h3 style={{ color: "var(--accent)", fontSize: "14px", marginBottom: "8px" }}>
            🧠 AI Insights
          </h3>
          {data.ai_suggestions.map((s, i) => (
            <div key={i} style={{ marginBottom: "6px", fontSize: "13px" }}>
              • {s}
            </div>
          ))}
        </div>
      )}

      {ollamaEnabled && !data.ai_suggestions && (
        <div style={{ marginTop: "12px" }}>
          <button className="btn-sm" style={{ fontSize: "12px" }} onClick={onGenerate}>
            Enhance with AI
          </button>
        </div>
      )}
    </div>
  );
}
