// Grocery list card: generates the list from the current weekly menu and renders
// it grouped by category with per-item quantities, plus export links.
// Includes audit B3a: user-added "extras" (e.g. Oreos, milk) attached to the
// current week's menu and folded into the categorized list + exports.

import { useState, useEffect } from "react";
import { apiFetch } from "../api.js";

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

const linkBtn = { ...btn, display: "inline-block", textDecoration: "none", textAlign: "center" };

const input = {
  display: "block",
  width: "100%",
  marginBottom: "10px",
  padding: "8px",
  borderRadius: "6px",
  border: "1px solid #333",
  background: "#2a2a2a",
  color: "#fff"
};

const itemRow = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "4px 0",
  borderBottom: "1px solid #333"
};

const smallBtn = { ...btn, padding: "2px 6px", fontSize: "11px" };
const errText = { color: "#fecaca", fontSize: "12px", marginTop: "4px" };

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
      body: JSON.stringify({ items: next })
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
      body: JSON.stringify({ items: next })
    })
      .then((r) => {
        setExtras(r.extras);
        onGenerate();
      })
      .catch((e) => setErr(e.message));
  };

  return (
    <div style={card}>
      <h2>Grocery List</h2>
      <button style={btn} onClick={onGenerate}>Generate Grocery</button>

      {grocery && (
        <>
          <a style={linkBtn} href="/grocery/export?format=csv" download>Download CSV</a>
          <span style={{ margin: "0 8px", opacity: 0.5 }}>|</span>
          <a style={linkBtn} href="/grocery/export?format=text" download>Download Text</a>
          <span style={{ margin: "0 8px", opacity: 0.5 }}>|</span>
          <a
            style={linkBtn}
            href={`mailto:?subject=My%20Shopping%20List&body=${encodeURIComponent(
              Object.entries(grocery)
                .map(([category, items]) =>
                  `${category.toUpperCase()}\n${items.map((i) => `  - ${i.item} (${i.qty})`).join("\n")}`
                )
                .join("\n\n") || "My shopping list is empty."
            )}`}
          >
            Email list
          </a>

          {/* audit B3a — custom grocery items */}
          <div style={{ marginTop: "15px" }}>
            <input
              style={input}
              placeholder="Add item (e.g. Oreos)"
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addExtra()}
            />
            <button style={{ ...smallBtn, marginLeft: "6px" }} onClick={addExtra}>Add</button>
            {err && <span style={errText}>{err}</span>}

            {Array.isArray(extras) && extras.length > 0 ? (
              <ul style={{ listStyle: "none", padding: 0, marginTop: "8px" }}>
                {extras.map((item) => (
                  <li key={item} style={itemRow}>
                    <span>{item}</span>
                    <button style={smallBtn} onClick={() => removeExtra(item)}>✕</button>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ opacity: 0.6, marginTop: "8px", fontSize: "13px" }}>
                No custom items yet.
              </p>
            )}
          </div>

          <div style={{ marginTop: "15px" }}>
            {Object.entries(grocery).map(([category, items]) => (
              <div key={category} style={{ marginBottom: "15px" }}>
                <h3 style={{ color: "#9ca3af" }}>{category}</h3>
                <ul style={{ paddingLeft: "15px" }}>
                  {items.map((i) => (
                    <li key={i.item}>
                      {i.item} <span style={{ opacity: 0.6 }}>({i.qty})</span>
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
