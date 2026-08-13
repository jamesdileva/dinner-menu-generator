// Grocery list card: generates the list from the current weekly menu and renders
// it grouped by category with per-item quantities, plus export links.
// §13a.4: "Email list" mailto link (pre-existing) + CSV / text downloads.
// §13.3: checkboxes + strikethrough for checked-off items; persisted per-menu.
// §13.3b: saved-grocery catalog (snacks + staples) displayed as collapsible
//        badges at the top — click ＋ to add a saved item to the current week's list.

import { useState, useEffect } from "react";
import { apiFetch } from "../api.js";

export default function GroceryList({ grocery, onGenerate, savings: savingsProp, onSavingsChange, ollamaEnabled, enhancedGrocery, onEnhance, enhancing }) {
  const [extras, setExtras] = useState(null);
  const [, setErr] = useState("");
  // §13.3b — savings comes from App.jsx (shared state) so snack/staple additions
  // show up immediately without a manual refresh.
  const savings = savingsProp || [];

  const loadExtras = () =>
    apiFetch("/grocery/extras")
      .then((r) => setExtras(r.extras || []))
      .catch((e) => setErr(e.message));

  const loadSavings = onSavingsChange || (() => {});

  // keep the extra-items list in sync with the latest grocery generation
  useEffect(() => {
    if (grocery) loadExtras();
  }, [grocery]);

  // §13.3b — when a saved-grocery item is clicked, add it to the current week's extras
  const addExtra = (name) => {
    const n = name.trim();
    if (!n) return;
    const next = [...(extras || []), n];
    apiFetch("/grocery/extras", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: next }),
    })
      .then((r) => {
        setExtras(r.extras);
        onGenerate();
      })
      .catch((e) => setErr(e.message));
  };

    

  // §13.3b — click a saved-grocery badge to add it to the current week's extras
  const addFromCatalog = (name) => {
    addExtra(name);
  };

  // §13.3b — delete a saved-grocery item from the catalog
  const deleteSaving = (id) => {
    apiFetch(`/saving/${id}`, { method: "DELETE" })
      .then(() => loadSavings())
      .catch((e) => setErr(e.message));
  };

  // §13.3 — toggle a single item's checked-off state
  const toggleItem = (itemName) => {
    apiFetch(`/grocery/purchased/${encodeURIComponent(itemName)}`, { method: "POST" })
      .then(() => {
        onGenerate();
      })
      .catch((e) => setErr(e.message));
  };

  // §13.3 — build the text/CSV body with checked/unchecked annotation
  const textBody = () => {
    if (!grocery) return "My shopping list is empty.";
    return Object.entries(grocery)
      .map(([category, items]) =>
        `${category.toUpperCase()}\n${items
          .map((i) => `  ${i.purchased ? "[x]" : "[ ]"} ${i.item} (${i.qty})`)
          .join("\n")}`
      )
      .join("\n\n");
  };

  const snacks = savings.filter((s) => s.group === "snacks");
  const staples = savings.filter((s) => s.group === "staples");

  // §13.23 — track which saved-grocery sections are expanded in the grocery list
  const [expandedSections, setExpandedSections] = useState({ snacks: true, staples: true });

  const toggleSection = (section) => {
    setExpandedSections((p) => ({ ...p, [section]: !p[section] }));
  };

  return (
    <div className="card">
      <h2>Grocery List</h2>
      <button className="btn" onClick={onGenerate}>
        Generate Grocery
      </button>

      {grocery && (
      <>
        {/* §13.23 — collapsible saved groceries at the top of the grocery list */}
        {savings.length > 0 && (
          <div style={{ marginTop: "15px" }}>
            {[
              { key: "snacks", label: "Snacks", items: snacks },
              { key: "staples", label: "Staples", items: staples },
            ].map(({ key, label, items }) =>
              items.length > 0 ? (
                <div key={key} style={{ marginTop: "12px" }}>
                  <div
                    className="row-between"
                    style={{ cursor: "pointer", marginBottom: "6px" }}
                    onClick={() => toggleSection(key)}
                  >
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                      🛒 Saved {label.toLowerCase()} ({items.length})
                    </span>
                    <span style={{ fontSize: "14px", color: "var(--text-muted)" }}>
                      {expandedSections[key] ? "▴" : "▾"}
                    </span>
                  </div>
                  {expandedSections[key] && (
                    <div
                      className="row-gap"
                      style={{ gap: "6px", flexWrap: "wrap", alignItems: "center" }}
                    >
                      {items.map((s) => (
                        <div
                          key={s.id}
                          className="row-gap"
                          style={{ gap: "2px", alignItems: "center" }}
                        >
                          <button
                            className="btn-sm"
                            style={{
                              background: "var(--bg-panel)",
                              border: "1px solid var(--border)",
                              borderRadius: "4px",
                              padding: "4px 8px",
                              fontSize: "13px",
                              color: "var(--text-h)",
                              cursor: "pointer",
                            }}
                            onClick={() => addFromCatalog(s.name)}
                            title={`Add ${s.name} to this week's list`}
                          >
                            + {s.name}
                          </button>
                          <button
                            className="btn-sm"
                            style={{
                              background: "transparent",
                              border: "none",
                              padding: 0,
                              fontSize: "13px",
                              color: "var(--text-muted)",
                              cursor: "pointer",
                            }}
                            onClick={() => deleteSaving(s.id)}
                            title={`Remove ${s.name} from saved groceries`}
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : null
            )}
          </div>
        )}

        {/* Export links */}
        <div className="row-gap" style={{ marginTop: "12px", gap: "8px", flexWrap: "wrap" }}>
          <a className="link-btn" href="/grocery/export?format=csv" download>
            Download CSV
          </a>
          <span style={{ opacity: 0.5 }}>|</span>
          <a className="link-btn" href="/grocery/export?format=text" download>
            Download Text
          </a>
          <span style={{ opacity: 0.5 }}>|</span>
          <button
            className="link-btn"
            onClick={() => window.open(
              `mailto:?subject=My%20Shopping%20List&body=${encodeURIComponent(textBody())}`,
              "_blank"
            )}
          >
            Email list
          </button>
          {/* §16.2 — AI-enhanced grocery list */}
          {ollamaEnabled && (
            <>
              <span style={{ opacity: 0.5 }}>|</span>
              <button
                className="btn-sm"
                style={{ fontSize: "13px" }}
                onClick={onEnhance}
                disabled={enhancing}
                title="Reorganize into store layout + suggest missing items"
              >
                {enhancing ? "Enhancing…" : "🧠 Enhance"}
              </button>
            </>
          )}
        </div>

        {/* §16.2 — enhanced grocery list (if available, show alongside original) */}
        {enhancedGrocery && (
          <div style={{ marginTop: "15px" }}>
            <h3 style={{ color: "var(--accent)", fontSize: "14px", marginBottom: "8px" }}>
              🧠 AI-Optimized List
            </h3>
            <div className="grocery-scroll">
              {Object.entries(enhancedGrocery).map(([category, items]) => (
                <div key={category} style={{ marginBottom: "12px" }}>
                  <h4 style={{ color: "var(--text-muted)", fontSize: "13px" }}>{category}</h4>
                  <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                    {items.map((i) => (
                      <li key={i.item} className="list-item" style={{ padding: "4px 0" }}>
                        <span className="row-gap" style={{ gap: "6px" }}>
                          <span>{i.item}</span>
                          {i.qty && <span style={{ opacity: 0.6 }}>({i.qty})</span>}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <button
              className="btn-sm"
              style={{ fontSize: "12px", marginTop: "8px" }}
              onClick={() => onGenerate()}
              title="Replace original list with the AI-enhanced version"
            >
              Use This
            </button>
          </div>
        )}

        {/* §16.2 — scrollable categorized items with checkboxes */}
        <div style={{ marginTop: "15px" }}>
          <div className="grocery-scroll">
            {Object.entries(grocery).map(([category, items]) => (
              <div key={category} style={{ marginBottom: "15px" }}>
                <h3 style={{ color: "var(--text-muted)" }}>{category}</h3>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {items.map((i) => (
                    <li
                      key={i.item}
                      className="list-item"
                      style={{
                        textDecoration: i.purchased ? "line-through" : "none",
                        opacity: i.purchased ? 0.6 : 1,
                      }}
                    >
                      <span className="row-gap" style={{ gap: "8px" }}>
                        <input
                          type="checkbox"
                          checked={!!i.purchased}
                          onChange={() => toggleItem(i.item)}
                          style={{ cursor: "pointer" }}
                        />
                        <span>{i.item}</span>
                        <span style={{ opacity: 0.6 }}>({i.qty})</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </>

      )}
    </div>
  );
}