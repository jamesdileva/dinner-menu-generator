// Grocery list card: generates the list from the current weekly menu and renders
// it grouped by category with per-item quantities, plus export links.
// Includes audit B3a: user-added "extras" (e.g. Oreos, milk) attached to the
// current week's menu and folded into the categorized list + exports.
// §13a.4: "Email list" mailto link (pre-existing) + CSV / text downloads.
// §13.3: checkboxes + strikethrough for checked-off items; persisted per-menu.

import { useState, useEffect } from "react";
import { apiFetch } from "../api.js";

export default function GroceryList({ grocery, onGenerate }) {
  const [extras, setExtras] = useState(null);
  const [extra, setExtra] = useState("");
  const [err, setErr] = useState("");

  const loadExtras = () =>
    apiFetch("/grocery/extras")
      .then((r) => setExtras(r.extras || []))
      .catch((e) => setErr(e.message));

  // keep the extra-items list in sync with the latest grocery generation
  useEffect(() => {
    if (grocery) loadExtras();
  }, [grocery]);

  const addExtra = () => {
    const name = extra.trim();
    if (!name) return;
    const next = [...(extras || []), name];
    apiFetch("/grocery/extras", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: next }),
    })
      .then((r) => {
        setExtras(r.extras);
        setExtra("");
        onGenerate(); // refresh the categorized list so the extra appears
      })
      .catch((e) => setErr(e.message));
  };

  const removeExtra = (item) => {
    const next = (extras || []).filter((x) => x !== item);
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

  // §13.3 — toggle a single item's checked-off state
  const toggleItem = (itemName) => {
    apiFetch(`/grocery/purchased/${encodeURIComponent(itemName)}`, { method: "POST" })
      .then(() => {
        // optimistic: refresh the grocery list to pick up the new purchased state
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

  return (
    <div className="card">
      <h2>Grocery List</h2>
      <button className="btn" onClick={onGenerate}>
        Generate Grocery
      </button>

      {grocery && (
        <>
          <div className="row-gap" style={{ marginTop: "12px", gap: "8px", flexWrap: "wrap" }}>
            <a className="link-btn" href="/grocery/export?format=csv" download>
              Download CSV
            </a>
            <span style={{ opacity: 0.5 }}>|</span>
            <a className="link-btn" href="/grocery/export?format=text" download>
              Download Text
            </a>
            <span style={{ opacity: 0.5 }}>|</span>
            <a
              className="link-btn"
              href={`mailto:?subject=My%20Shopping%20List&body=${encodeURIComponent(textBody())}`}
            >
              Email list
            </a>
          </div>

          {/* audit B3a — custom grocery items */}
          <div style={{ marginTop: "15px" }}>
            <input
              className="input-field"
              placeholder="Add item (e.g. Oreos)"
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addExtra()}
            />
            <div className="row-gap" style={{ gap: "6px" }}>
              <button className="btn-sm" onClick={addExtra}>
                Add
              </button>
            </div>
            {err && (
              <span
                style={{ color: "var(--text-error)", fontSize: "12px", marginTop: "4px", display: "block" }}
              >
                {err}
              </span>
            )}

            {Array.isArray(extras) && extras.length > 0 ? (
              <ul style={{ listStyle: "none", padding: 0, marginTop: "8px" }}>
                {extras.map((item) => (
                  <li key={item} className="list-item">
                    <span>{item}</span>
                    <button className="btn-sm" onClick={() => removeExtra(item)}>
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ opacity: 0.6, marginTop: "8px", fontSize: "13px" }}>
                No custom items yet.
              </p>
            )}
          </div>

          {/* §13.3 — categorized items with checkboxes */}
          <div style={{ marginTop: "15px" }}>
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
        </>
      )}
    </div>
  );
}
