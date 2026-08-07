// Add-meal card: text inputs + "Add Meal" button + OCR image upload.
// All async logic (name/ingredients state, add, upload) is owned by the parent App
// and passed in as props so error/loading stay in one place.

export default function AddMeal({ name, ingredients, category, categories, onNameChange, onIngredientsChange, onCategoryChange, onAdd, onUpload }) {
  return (
    <div className="card">
      <h2>Add Meal</h2>
      <input
        className="input-field"
        placeholder="Meal name"
        value={name}
        onChange={onNameChange}
      />
      <select className="input-field" value={category || ""} onChange={onCategoryChange}>
        <option value="">(no category)</option>
        {categories.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <input
        className="input-field"
        placeholder="Ingredients (comma separated)"
        value={ingredients}
        onChange={onIngredientsChange}
      />

      <div className="row-wrap" style={{ gap: "10px" }}>
        <button className="btn" onClick={onAdd}>
          Add Meal
        </button>
        <input type="file" onChange={onUpload} />
      </div>
    </div>
  );
}
