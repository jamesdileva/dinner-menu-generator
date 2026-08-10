// ManageMeals card (audit §13.21): browse meals (paginated), edit inline, delete with undo.
// §13.23: tabs switch between Meals list, Saved Snacks, and Saved Staples.
// The state (editingMeal, editName, etc.) and handlers live in App.jsx and are passed
// in as props/caller functions.

import { useState } from "react";


export default function ManageMeals({
  meals, mealsPage, mealsPages, mealsTotal,
  categories, editingMeal, editName, editIngredients, editCategory,
  onEditMeal, onCancelEdit, onSaveEdit, onDeleteMeal,
  onPageChange, onCategoryFilter, onSearch,
  onEditNameChange, onEditIngredientsChange, onEditCategoryChange,
  savings, onAddFromSavings, onDeleteSaving,
}) {
  const [activeTab, setActiveTab] = useState("meals");

  const tabs = [
    { id: "meals", label: "Meals" },
    { id: "snacks", label: "Snacks" },
    { id: "staples", label: "Staples" },
  ];

  const snacks = savings.filter((s) => s.group === "snacks");
  const staples = savings.filter((s) => s.group === "staples");

  return (
    <div className="card">
      <h2>All Meals</h2>

      <div className="row-gap" style={{ marginBottom: "10px" }}>
        {tabs.map((t) => (
          <button
            key={t.id}
            className="btn-sm"
            style={{
              background: activeTab === t.id ? "var(--accent)" : "var(--bg-panel)",
              color: activeTab === t.id ? "#fff" : "var(--text-muted)",
              padding: "4px 10px",
              fontSize: "13px",
            }}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "meals" && (
        <>
          <div className="row-gap" style={{ marginBottom: "10px" }}>
            <span>Category:</span>
            <select className="input-field-sm" value={""} onChange={onCategoryFilter}>
              <option value="">All</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <input
            className="input-field"
            placeholder="Search meals…"
            onChange={onSearch}
          />

          <ul style={{ listStyle: "none", padding: 0 }}>
            {meals.map((meal) => (
              <li key={meal.id} className="list-item">
                {editingMeal?.id === meal.id ? (
                  <div style={{ display: "block", width: "100%" }}>
                    <input
                      className="input-field"
                      value={editName}
                      onChange={onEditNameChange}
                      onKeyDown={(e) => e.key === "Enter" && onSaveEdit(meal)}
                      placeholder="Meal name"
                    />
                    <input
                      className="input-field"
                      value={editIngredients}
                      onChange={onEditIngredientsChange}
                      onKeyDown={(e) => e.key === "Enter" && onSaveEdit(meal)}
                      placeholder="Ingredients (comma separated)"
                    />
                    <select className="input-field" style={{ marginBottom: "8px" }} value={editCategory || ""} onChange={onEditCategoryChange}>
                      <option value="">(no category)</option>
                      {categories.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                    <div className="row-gap" style={{ gap: "8px" }}>
                      <button className="btn-sm" onClick={() => onSaveEdit(meal)}>Save</button>
                      <button className="btn-sm" onClick={onCancelEdit}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <span>
                      {meal.name}
                      {meal.category ? <span className="category-chip">{meal.category}</span> : null}
                    </span>
                    <div>
                      <button className="btn-sm" onClick={() => onEditMeal(meal)}>Edit</button>
                      <button className="btn-sm" onClick={() => onDeleteMeal(meal)}>Delete</button>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>

          <div className="row-between" style={{ marginTop: "10px", fontSize: "13px", color: "var(--text-muted)" }}>
            <span>Page {mealsPage}/{mealsPages} ({mealsTotal} meals)</span>
            <div className="row-gap" style={{ gap: "6px" }}>
              <button className="btn-sm" onClick={() => onPageChange(mealsPage - 1)} disabled={mealsPage <= 1}>Prev</button>
              <button className="btn-sm" onClick={() => onPageChange(mealsPage + 1)} disabled={mealsPage >= mealsPages}>Next</button>
            </div>
          </div>
        </>
      )}

      {(activeTab === "snacks" || activeTab === "staples") && (
        <div style={{ maxHeight: "400px", overflowY: "auto" }}>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {(activeTab === "snacks" ? snacks : staples).map((s) => (
              <li key={s.id} className="list-item">
                <span>{s.name}</span>
                <div>
                  <button className="btn-sm" onClick={() => onAddFromSavings(s.name)}>+</button>
                  <button className="btn-sm" onClick={() => onDeleteSaving(s.id)}>×</button>
                </div>
              </li>
            ))}
            {(activeTab === "snacks" ? snacks : staples).length === 0 && (
              <p style={{ opacity: 0.6, fontSize: "13px", marginTop: "8px" }}>
                No {activeTab} saved yet.
              </p>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
