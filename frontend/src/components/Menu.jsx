// Weekly menu card: generates the week, lists each day, rerolls individual days.
// §5.17: each day's meal name toggles its ingredients. §13a.4: "Email this menu"
// builds a mailto body from the 7-day plan (mirrors GroceryList's email link).

import { useState } from "react";

const dayOrder = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function Menu({ menu, onGenerate, onReroll }) {
  const [openDay, setOpenDay] = useState(null); // §5.17 ingredient detail toggle

  // §13a.4 — build a mailto: body with the 7-day plan
  const emailBody = menu
    ? dayOrder
        .map((day) => {
          const meal = menu[day];
          if (!meal || !meal.name) return `${day}: —`;
          const ing = meal.ingredients && meal.ingredients.length
            ? ` — ${meal.ingredients.join(", ")}`
            : "";
          return `${day}: ${meal.name}${ing}`;
        })
        .join("\n")
    : "";

  return (
    <div className="card">
      <h2>Weekly Menu</h2>
      <div className="row-wrap" style={{ gap: "10px", marginBottom: "10px" }}>
        <button className="btn" onClick={onGenerate}>
          Generate Week
        </button>
      </div>

      {menu && (
        <>
          <button
            className="link-btn"
            style={{ marginRight: "8px" }}
            onClick={() => window.open(
              `mailto:?subject=My%20Weekly%20Menu&body=${encodeURIComponent(emailBody)}`,
              "_blank"
            )}
          >
            Email this menu
          </button>

          <ul style={{ listStyle: "none", padding: 0, marginTop: "10px" }}>
            {dayOrder.map((day) => {
              const meal = menu[day];
              const isOpen = openDay === day;
              return (
                <li key={day} className="list-item">
                  <span>
                    <strong style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                      {day}
                    </strong>
                    :{" "}
                    <button
                      className="btn-sm"
                      style={{
                        background: "transparent",
                        color: "var(--text-h)",
                        textDecoration: "underline",
                        padding: 0,
                        margin: 0,
                        cursor: meal?.name ? "pointer" : "default",
                      }}
                      onClick={() => meal?.name && setOpenDay(isOpen ? null : day)}
                    >
                      {meal?.name ?? "—"}
                    </button>
                  </span>
                  <div>
                    <button className="btn-sm" onClick={() => onReroll(day)}>
                      Reroll
                    </button>
                  </div>
                  {isOpen && meal?.ingredients && meal.ingredients.length ? (
                    <ul
                      style={{
                        listStyle: "disc",
                        padding: "4px 0 0 18px",
                        margin: 0,
                        opacity: 0.8,
                        fontSize: "13px",
                        width: "100%",
                      }}
                    >
                      {meal.ingredients.map((ing, i) => (
                        <li key={i}>{ing}</li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}
