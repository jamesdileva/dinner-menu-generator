// Calendar view (audit B1): read-only week-tiles of every saved weekly menu,
// newest first. Each menu is a Mon–Sun grid; clicking a meal name expands its
// ingredients inline (mirrors Menu.jsx's toggle). Reuses the same /menus fetch
// as History (shared `menus`/`onGenerate` props in App.jsx).
import { useState } from "react";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function Calendar({ menus }) {
  // track which meal-name cell is expanded to show ingredients
  const [openCell, setOpenCell] = useState(null); // "menuId|day" or null
  function toggle(dayId) {
    setOpenCell((open) => (open === dayId ? null : dayId));
  }

  if (menus === null) {
    return (
      <div className="card">
        <h2>Calendar</h2>
        <p style={{ opacity: 0.7, marginTop: "8px", fontSize: "13px" }}>
          Click "Load History" in the Past Menus card to view the calendar.
        </p>
      </div>
    );
  }

  if (menus.length === 0) {
    return (
      <div className="card">
        <h2>Calendar</h2>
        <p style={{ opacity: 0.7, marginTop: "8px" }}>No menus generated yet.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Calendar</h2>
      {menus.map((menu) => (
        <div key={menu.id} className="calendar-panel">
          <strong style={{ marginBottom: "8px", display: "block" }}>Menu #{menu.id}</strong>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(7, 1fr)",
              gap: "4px",
            }}
          >
            {DAYS.map((day) => {
              const meal = menu.meals?.[day];
              const cellId = `${menu.id}|${day}`;
              const isOpen = openCell === cellId;
              const name = meal?.name ?? null;
              return (
                <div key={day}>
                  <div
                    style={{
                      border: "1px solid var(--border)",
                      borderRadius: "6px",
                      padding: "6px 8px",
                      minHeight: "44px",
                      cursor: name ? "pointer" : "default",
                      background: name ? "var(--bg-panel)" : "transparent",
                      opacity: name ? 1 : 0.5,
                    }}
                  >
                    <div
                      style={{
                        fontSize: "11px",
                        color: "var(--text-muted)",
                        textTransform: "uppercase",
                        letterSpacing: "0.04em",
                      }}
                    >
                      {day}
                    </div>
                    {name ? (
                      <div
                        style={{ fontWeight: 600, cursor: "pointer" }}
                        onClick={() => toggle(cellId)}
                      >
                        {meal?.category ? (
                          <span
                            style={{
                              display: "inline-block",
                              width: "8px",
                              height: "8px",
                              borderRadius: "50%",
                              background: "var(--accent)",
                              marginRight: "6px",
                              verticalAlign: "middle",
                            }}
                          />
                        ) : null}
                        {name}
                        {meal?.ingredients?.length ? (
                          <span
                            style={{ opacity: 0.5, marginLeft: "4px" }}
                          >
                            {isOpen ? "▴" : "▾"}
                          </span>
                        ) : null}
                      </div>
                    ) : (
                      <span style={{ opacity: 0.5 }}>—</span>
                    )}
                  </div>
                  {isOpen && meal?.ingredients?.length ? (
                    <ul
                      style={{
                        listStyle: "disc",
                        padding: "4px 0 4px 18px",
                        margin: 0,
                        opacity: 0.9,
                      }}
                    >
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
