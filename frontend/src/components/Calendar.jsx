// Calendar view (audit B1): read-only week-tiles of every saved weekly menu,
// newest first. Each menu is a Mon–Sun grid; clicking a meal name expands its
// ingredients inline (mirrors Menu.jsx's toggle). Reuses the same /menus fetch
// as History (shared `menus`/`onGenerate` props in App.jsx).
import { useState } from "react";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

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

const dayCell = {
  border: "1px solid #333",
  borderRadius: "6px",
  padding: "6px 8px",
  minHeight: "44px",
  cursor: "pointer",
  background: "#252526"
};

const dayLabel = {
  fontSize: "11px",
  color: "#9ca3af",
  textTransform: "uppercase",
  letterSpacing: "0.04em"
};

const ingredientList = {
  listStyle: "disc",
  padding: "4px 0 4px 18px",
  margin: 0,
  opacity: 0.9
};

const catDot = {
  display: "inline-block",
  width: "8px",
  height: "8px",
  borderRadius: "50%",
  background: "#3b82f6",
  marginRight: "6px",
  verticalAlign: "middle"
};

export default function Calendar({ menus, onGenerate }) {
  // track which meal-name cell is expanded to show ingredients
  const [openCell, setOpenCell] = useState(null); // "menuId|day" or null
  function toggle(dayId) {
    setOpenCell(open => (open === dayId ? null : dayId));
  }

  if (menus === null) {
    return (
      <div style={card}>
        <h2>Calendar</h2>
        <button style={btn} onClick={onGenerate}>Load Calendar</button>
      </div>
    );
  }

  if (menus.length === 0) {
    return (
      <div style={card}>
        <h2>Calendar</h2>
        <p style={{ opacity: 0.7, marginTop: "8px" }}>No menus generated yet.</p>
      </div>
    );
  }

  return (
    <div style={card}>
      <h2>Calendar</h2>
      {menus.map((menu) => (
        <div
          key={menu.id}
          style={{
            marginTop: "12px",
            padding: "8px",
            background: "#2a2a2a",
            borderRadius: "6px"
          }}
        >
          <strong style={{ opacity: 0.8, marginBottom: "8px", display: "block" }}>
            Menu #{menu.id}
          </strong>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(7, 1fr)",
            gap: "4px"
          }}>
            {DAYS.map((day) => {
              const meal = menu.meals?.[day];
              const cellId = `${menu.id}|${day}`;
              const isOpen = openCell === cellId;
              const name = meal?.name ?? null;
              return (
                <div key={day}>
                  <div style={{ ...dayCell, ...(name ? {} : { cursor: "default", opacity: 0.5 }) }}>
                    <div style={dayLabel}>{day}</div>
                    {name ? (
                      <div
                        style={{ fontWeight: 600, cursor: "pointer" }}
                        onClick={() => toggle(cellId)}
                      >
                        {meal?.category ? <><span style={catDot} />{meal.category} </> : null}
                        {name}
                        {meal?.ingredients?.length ? (
                          <span style={{ opacity: 0.5, marginLeft: "4px" }}>
                            {isOpen ? "▴" : "▾"}
                          </span>
                        ) : null}
                      </div>
                    ) : (
                      <span style={{ opacity: 0.5 }}>—</span>
                    )}
                  </div>
                  {isOpen && meal?.ingredients?.length ? (
                    <ul style={ingredientList}>
                      {meal.ingredients.map((ing, i) => (
                        <li key={i}>{ing}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
