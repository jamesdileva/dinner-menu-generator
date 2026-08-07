// Insights tab (audit B2): last-few-weeks macro overview + deficiency flags +
// rule-based swap suggestions. Lazy-fetches GET /insights (no backend DB writes).

const card = {
  background: "#1e1e1e",
  padding: "15px",
  borderRadius: "10px",
  marginBottom: "20px",
  boxShadow: "0 0 10px rgba(0,0,0,0.3)"
};

const btn = {
  background: "#3b82f6",
  border: "none",
  padding: "8px 12px",
  borderRadius: "6px",
  color: "white",
  cursor: "pointer"
};

const barWrap = { marginTop: "8px", marginBottom: "6px" };
const barRow = { display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" };
const barTrack = { flex: 1, height: "12px", background: "#2a2a2a", borderRadius: "6px", overflow: "hidden" };
const barFill = { height: "100%", background: "#3b82f6", borderRadius: "6px" };
const flag = { color: "#fbbf24", marginBottom: "4px" };
const suggestion = { color: "#86efac", marginBottom: "6px" };

export default function Insights({ data, onGenerate }) {
  if (data === null) {
    return (
      <div style={card}>
        <h2>Insights</h2>
        <button style={btn} onClick={onGenerate}>Load Insights</button>
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
    <div style={card}>
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
              <div style={barRow}>
                <span style={{ width: "110px", fontSize: "13px", color: "#9ca3af" }}>{macro}</span>
                <span style={{ fontSize: "12px", opacity: 0.8 }}>{total}/{t}</span>
              </div>
              <div style={barTrack}>
                <div
                  style={{ ...barFill, width: `${Math.min(pct, 100)}%`, background: pct >= 100 ? "#22c55e" : "#3b82f6" }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {data.flags && data.flags.length > 0 ? (
        <div style={{ marginTop: "12px" }}>
          <h3 style={{ color: "#9ca3af", fontSize: "14px" }}>Needs attention</h3>
          {data.flags.map((f) => (
            <div key={f} style={flag}>• {f}</div>
          ))}
        </div>
      ) : (
        <div style={{ marginTop: "12px", color: "#86efac" }}>• Looking balanced</div>
      )}

      <div style={{ marginTop: "12px" }}>
        <h3 style={{ color: "#9ca3af", fontSize: "14px" }}>Swap suggestions</h3>
        {(data.suggestions || []).map((s, i) => (
          <div key={i} style={suggestion}>• {s}</div>
        ))}
      </div>
    </div>
  );
}
