// §16.4 — AI meal suggestion modal.
// Shows 3 AI-generated meal ideas (name + ingredients + recipe), each with a
// "Save to Meals" button. Falls back gracefully when Ollama is disabled.

export default function SuggestMealModal({ open, onClose, suggestions, onSuggest, loading, onSave, ollamaEnabled }) {
  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxHeight: "85vh" }}>
        <div className="row-between" style={{ marginBottom: "12px" }}>
          <h2 style={{ margin: 0, fontSize: "20px" }}>AI Meal Suggestions</h2>
          <button
            className="btn-sm"
            style={{
              background: "transparent",
              border: "none",
              fontSize: "18px",
              cursor: "pointer",
              color: "var(--text-muted)",
              padding: "0 4px",
            }}
            onClick={onClose}
          >
            ×
          </button>
        </div>

        {!ollamaEnabled && (
          <div style={{ marginBottom: "12px", padding: "8px", background: "var(--bg-panel)", borderRadius: "6px", fontSize: "13px" }}>
            AI suggestions are disabled. Toggle "🧠 AI On" in the header and ensure Ollama is running
            (e.g. <code style={{ background: "var(--code-bg)", padding: "2px 6px", borderRadius: "4px" }}>ollama run llama3.1:8b</code>).
          </div>
        )}

        {suggestions === null && ollamaEnabled && (
          <p style={{ opacity: 0.6, fontSize: "13px" }}>Generating suggestions…</p>
        )}

        {suggestions === null && !ollamaEnabled && (
          <p style={{ opacity: 0.6, fontSize: "13px" }}>Enable AI features to get meal suggestions.</p>
        )}

        {suggestions && suggestions.length === 0 && ollamaEnabled && (
          <p style={{ opacity: 0.6, fontSize: "13px" }}>
            No suggestions available. Ollama may have returned an unexpected response.
          </p>
        )}

        {suggestions && suggestions.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {suggestions.map((s, i) => (
              <div key={i} style={{ padding: "10px", background: "var(--bg-panel)", borderRadius: "8px" }}>
                <strong style={{ fontSize: "14px", display: "block", marginBottom: "6px" }}>{s.name}</strong>
                <div style={{ fontSize: "13px", opacity: 0.8, marginBottom: "6px" }}>
                  <strong>Ingredients:</strong>{" "}
                  {Array.isArray(s.ingredients) && s.ingredients.length
                    ? s.ingredients.join(", ")
                    : "—"}
                </div>
                {s.recipe && (
                  <div style={{ fontSize: "13px", opacity: 0.7, marginBottom: "8px" }}>
                    <strong>Recipe:</strong> {s.recipe}
                  </div>
                )}
                <button className="btn-sm" style={{ fontSize: "12px" }} onClick={() => onSave(s)}>
                  Save to Meals
                </button>
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: "12px" }}>
          <button
            className="btn"
            style={{ fontSize: "13px" }}
            onClick={onSuggest}
            disabled={loading || !ollamaEnabled}
          >
            {loading ? "Generating…" : "Generate New Suggestions"}
          </button>
          <button className="btn-sm" style={{ marginLeft: "8px" }} onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
