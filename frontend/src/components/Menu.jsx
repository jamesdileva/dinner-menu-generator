// Weekly menu card: generates the week, lists each day, rerolls individual days.

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

export default function Menu({ menu, onGenerate, onReroll }) {
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
              <span><strong>{day}:</strong> {meal.name}</span>
              <button style={btnSmall} onClick={() => onReroll(day)}>🔄</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
