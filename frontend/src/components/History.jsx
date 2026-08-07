// Menu history card (audit §5.15): shows all saved weekly menus, newest first.
// Each menu's stored meal ids are expanded server-side (§5.13) into full meal dicts.

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

export default function History({ history, onGenerate }) {
  return (
    <div style={card}>
      <h2>Menu History</h2>
      {history === null ? (
        <button style={btn} onClick={onGenerate}>Load History</button>
      ) : (
        history.length === 0 ? (
          <p style={{ opacity: 0.7, marginTop: "8px" }}>No menus generated yet.</p>
        ) : (
          history.map((menu) => (
            <div key={menu.id} style={{
              marginTop: "12px",
              padding: "8px",
              background: "#2a2a2a",
              borderRadius: "6px"
            }}>
              <strong style={{ opacity: 0.8 }}>Menu #{menu.id}</strong>
              <ul style={{ listStyle: "none", padding: 0, marginTop: "6px" }}>
                {Object.entries(menu.meals || {}).map(([day, meal]) => (
                  <li key={day} style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "4px 0",
                    borderBottom: "1px solid #333"
                  }}>
                    <span><strong>{day}:</strong> {meal?.name ?? "—"}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )
      )}
    </div>
  );
}
