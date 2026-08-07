// Menu history card (audit §5.15): shows all saved weekly menus, newest first.
// Each menu's stored meal ids are expanded server-side (§5.13) into full meal dicts.
// §13a.6: this component is rendered inside a tabbed container in App.jsx.

export default function History({ history }) {
  if (history === null) {
    return (
      <div className="card">
        <h2>Menu History</h2>
        <p style={{ opacity: 0.7, marginTop: "8px", fontSize: "13px" }}>
          Click "Load History" in the Past Menus card to view saved menus.
        </p>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="card">
        <h2>Menu History</h2>
        <p style={{ opacity: 0.7, marginTop: "8px" }}>No menus generated yet.</p>
      </div>
    );
  }

  return (
    <div>
      {history.map((menu) => (
        <div
          key={menu.id}
          className="history-panel"
        >
          <strong>Menu #{menu.id}</strong>
          <ul style={{ listStyle: "none", padding: 0, marginTop: "6px" }}>
            {Object.entries(menu.meals || {}).map(([day, meal]) => (
              <li
                key={day}
                className="list-item"
                style={{ padding: "4px 0" }}
              >
                <span>
                  <strong>{day}:</strong>{" "}
                  {meal?.name ?? "—"}
                </span>
                {meal?.category ? (
                  <span className="category-chip">{meal.category}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
