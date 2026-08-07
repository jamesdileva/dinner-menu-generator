// Weekly menu card: generates the week, lists each day, rerolls individual days.
// audit §5.17: each day's meal name is now a toggle that reveals its ingredients
// (no need to jump to the "All Meals" section just to see what's in a planned meal).

import { useState } from "react";

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

const btnSmall = {
  ...btn,
  padding: "4px 8px",
  marginLeft: "5px"
};

const nameBtn = {
  background: "transparent",
  border: "none",
  color: "#e5e5e5",
  padding: 0,
  margin: 0,
  cursor: "pointer",
  textDecoration: "underline"
};

export default function Menu({ menu, onGenerate, onReroll }) {
  const [openDay, setOpenDay] = useState(null);  // §5.17 ingredient detail toggle

  return (
    <div style={card}>
      <h2>Weekly Menu</h2>
      <button style={btn} onClick={onGenerate}>Generate Week</button>

      {menu && (
        <ul style={{ listStyle: "none", padding: 0, marginTop: "10px" }}>
          {Object.entries(menu).map(([day, meal]) => (
            <li
              key={day}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "8px 0",
                borderBottom: "1px solid #333"
              }}
            >
              <span>
                <strong>{day}:</strong>{" "}
                <button
                  style={nameBtn}
                  onClick={() => setOpenDay(openDay === day ? null : day)}  // §5.17 toggle
                >
                  {meal?.name ?? "—"}
                </button>
              </span>
              <div>
                <button style={btnSmall} onClick={() => onReroll(day)}>🔄</button>
              </div>
              {openDay === day && meal?.ingredients && (
                <ul style={{
                  listStyle: "disc inside",
                  margin: "6px 0 0 0",
                  padding: 0,
                  opacity: 0.8,
                  fontSize: "13px"
                }}>
                  {meal.ingredients.map((ing, i) => (
                    <li key={i}>{ing}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
