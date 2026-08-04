// Grocery list card: generates the list from the current weekly menu and renders
// it grouped by category with per-item quantities.

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

export default function GroceryList({ grocery, onGenerate }) {
  return (
    <div style={card}>
      <h2>Grocery List</h2>
      <button style={btn} onClick={onGenerate}>Generate Grocery</button>

      {grocery && (
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
      )}
    </div>
  );
}
