// Add-meal card: text inputs + "Add Meal" button + OCR image upload.
// All async logic (name/ingredients state, add, upload) is owned by the parent App
// and passed in as props so error/loading stay in one place.

const card = {
  background: "#1e1e1e",
  padding: "15px",
  borderRadius: "10px",
  marginBottom: "20px",
  boxShadow: "0 0 10px rgba(0,0,0,0.3)"
};

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

const btn = {
  background: "#3b82f6",
  border: "none",
  padding: "8px 12px",
  borderRadius: "6px",
  color: "white",
  cursor: "pointer"
};

export default function AddMeal({ name, ingredients, category, categories, onNameChange, onIngredientsChange, onCategoryChange, onAdd, onUpload }) {
  return (
    <div style={card}>
      <h2>Add Meal</h2>
      <input
        style={input}
        placeholder="Meal name"
        value={name}
        onChange={onNameChange}
      />
      <select style={input} value={category || ""} onChange={onCategoryChange}>
        <option value="">(no category)</option>
        {categories.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <input
        style={input}
        placeholder="Ingredients (comma separated)"
        value={ingredients}
        onChange={onIngredientsChange}
      />

      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <button style={btn} onClick={onAdd}>Add Meal</button>
        <input type="file" onChange={onUpload} />
      </div>
    </div>
  );
}
