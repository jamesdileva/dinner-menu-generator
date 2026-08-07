import { useState, useEffect, useRef } from "react";
import { apiFetch, MEALS_PER_PAGE } from "./api.js";
import Menu from "./components/Menu.jsx";
import GroceryList from "./components/GroceryList.jsx";
import AddMeal from "./components/AddMeal.jsx";
import History from "./components/History.jsx";
import Calendar from "./components/Calendar.jsx";
import Insights from "./components/Insights.jsx";

const card = {
  background: "#1e1e1e",
  padding: "15px",
  borderRadius: "10px",
  marginBottom: "20px",
  boxShadow: "0 0 10px rgba(0,0,0,0.3)"
};

const btnSmall = {
  background: "#3b82f6",
  border: "none",
  padding: "4px 8px",
  marginLeft: "5px",
  borderRadius: "6px",
  color: "white",
  cursor: "pointer"
};

const listItem = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "8px 0",
  borderBottom: "1px solid #333"
};

const resultBox = {
  marginTop: "15px",
  padding: "10px",
  background: "#2a2a2a",
  borderRadius: "8px"
};

const errorBanner = {
  background: "#7f1d1d",
  color: "#fee2e2",
  padding: "10px",
  borderRadius: "8px",
  marginBottom: "15px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center"
};

const spinner = {
  display: "inline-block",
  width: "14px",
  height: "14px",
  border: "2px solid #3b82f6",
  borderTopColor: "transparent",
  borderRadius: "50%",
  animation: "spin 0.7s linear infinite"
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

const undoBar = {
  background: "#1f2937",
  color: "#d1d5db",
  padding: "8px 12px",
  borderRadius: "8px",
  marginBottom: "12px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  fontSize: "14px"
};

const UNDO_WINDOW_MS = 6000;

export default function App() {
  const [menu, setMenu] = useState(null);
  const [name, setName] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [grocery, setGrocery] = useState(null);
   const [menuHistory, setMenuHistory] = useState(null); // §5.15
   const [insights, setInsights] = useState(null); // audit B2

  const [meals, setMeals] = useState([]);
  const [mealsPage, setMealsPage] = useState(1);
  const [mealsPages, setMealsPages] = useState(1);
  const [mealsTotal, setMealsTotal] = useState(0);
  const [today, setToday] = useState(null);
  const [takeout, setTakeout] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // §5.12: inline edit form (replaces prompt()) + undo toast for destructive actions
  const [editingMeal, setEditingMeal] = useState(null);
  const [editName, setEditName] = useState("");
  const [editIngredients, setEditIngredients] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [undo, setUndo] = useState(null); // { message, action } | null
  const undoTimer = useRef(null);

  // §5.14: add-meal category + meals list category filter
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [mealCategory, setMealCategory] = useState("");
  const [search, setSearch] = useState("");  // §5.18 meal name search

  // 4.2 centralised loading + error handling for async actions
  async function withLoading(fn) {
    setError(null);
    setLoading(true);
    try {
      await fn();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // §5.12: time-limited Undo toast; clears any previous timer automatically
  function showUndo(message, action) {
    if (undoTimer.current) clearTimeout(undoTimer.current);
    setUndo({ message, action });
    undoTimer.current = setTimeout(() => setUndo(null), UNDO_WINDOW_MS);
  }

  function runUndo() {
    if (undoTimer.current) clearTimeout(undoTimer.current);
    undoTimer.current = null;
    const action = undo?.action;
    setUndo(null);
    if (action) action();
  }

  function dismissUndo() {
    if (undoTimer.current) clearTimeout(undoTimer.current);
    undoTimer.current = null;
    setUndo(null);
  }

  useEffect(() => {
    return () => { if (undoTimer.current) clearTimeout(undoTimer.current); };
  }, []);

  const getTodayMeal = () => withLoading(async () => {
    setToday(await apiFetch("/menu/today"));
  });

  const getTakeout = () => withLoading(async () => {
    setTakeout(await apiFetch("/menu/takeout"));
  });

  const loadMenu = () => withLoading(async () => {
    const data = await apiFetch("/menu/week");
    setMenu(data);
    setGrocery(null); // reset grocery
  });

  const loadGrocery = () => withLoading(async () => {
    setGrocery(await apiFetch("/grocery"));
  });

   const loadHistory = () => withLoading(async () => {
     setMenuHistory(await apiFetch("/menus"));
   });

   const loadInsights = () => withLoading(async () => {
     setInsights(await apiFetch("/insights"));
   });


  const rerollDay = async (day) => {
    // §5.12: capture prior meal so Undo can restore it via PUT /menu/<day>
    const prevMeal = menu?.[day] ?? null;
    setError(null);
    setLoading(true);
    try {
      const data = await apiFetch(`/menu/reroll/${day}`, { method: "POST" });
      setMenu(prev => ({ ...prev, [day]: data.meal }));
      if (prevMeal) {
          showUndo(`Rolled "${prevMeal.name}" for ${day}; undo?`, () =>
          apiFetch(`/menu/${day}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(prevMeal)
          }).then(res => setMenu(p => ({ ...p, [day]: res.meal ?? prevMeal }))).catch(() => {})
        );
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const loadMeals = (page = 1) => withLoading(async () => {
    let url = `/meals?page=${page}&limit=${MEALS_PER_PAGE}`;
    if (mealCategory) url += `&category=${encodeURIComponent(mealCategory)}`;  // §5.14
    if (search) url += `&search=${encodeURIComponent(search)}`;  // §5.18
    const data = await apiFetch(url);
    setMeals(data.meals);
    setMealsPage(data.page);
    setMealsPages(data.pages);
    setMealsTotal(data.total);
  });

  const loadCategories = () => {  // §5.14 distinct category list for the filter dropdown
    apiFetch("/meals/categories").then(res => setCategories(res.categories)).catch(() => {});
  };

  const editMeal = (meal) => {
    // §5.12: open inline edit form instead of blocking prompt()
    setEditingMeal(meal);
    setEditName(meal.name);
    setEditIngredients(Array.isArray(meal.ingredients) ? meal.ingredients.join(", ") : "");
    setEditCategory(meal.category || "");
  };

  const cancelEdit = () => {
    setEditingMeal(null);
    setEditName("");
    setEditIngredients("");
    setEditCategory("");
  };

  const saveEdit = (meal) => withLoading(async () => {
    await apiFetch(`/meal/${meal.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: editName.trim(),
        ingredients: editIngredients.split(",").map(i => i.trim()).filter(Boolean),
        category: editCategory || undefined  // §5.14
      })
    });
    cancelEdit();
    loadMeals(mealsPage);
  });

  const uploadImage = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file);

    withLoading(async () => {
      const data = await apiFetch("/upload-menu", {
        method: "POST",
        body: formData
      });
      alert(
        `Added: ${data.added.length}\nUpdated: ${data.updated.length}\nSkipped: ${data.skipped.length}`
      );
      loadMeals(1);
    });
  };

   const deleteMeal = (meal) => withLoading(async () => {
    await apiFetch(`/meal/${meal.id}`, { method: "DELETE" });
    // §5.12: offer Undo; recreating needs the original meal object
    showUndo(`Deleted "${meal.name}"; undo?`, () =>
      apiFetch("/meal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: meal.id, name: meal.name, ingredients: meal.ingredients })
      }).then(() => loadMeals(mealsPage)).catch(() => {})
    );
    loadMeals(mealsPage);
  });

  const addMeal = () => withLoading(async () => {
    await apiFetch("/meal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        ingredients: ingredients.split(",").map(i => i.trim()),
        category: category || undefined  // §5.14
      })
    });
    setName("");
    setIngredients("");
    setCategory("");
    loadMeals(1);
  });

  useEffect(() => {
    loadMeals();
    loadCategories();  // §5.14
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{
      background: "#121212",
      color: "#e5e5e5",
      minHeight: "100vh",
      padding: "25px",
      fontFamily: "Arial",
      maxWidth: "900px",
      margin: "0 auto"
    }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      <h1 style={{ marginBottom: "25px" }}>🍽 Dinner Planner</h1>

      {error && (
        <div style={errorBanner}>
          <span>{error}</span>
          <button style={btnSmall} onClick={() => setError(null)}>✕</button>
        </div>
      )}
      {loading && (
        <div style={{ marginBottom: "10px" }}>Loading <span style={spinner}></span></div>
      )}

      {undo && (
        <div style={undoBar}>
          <span>{undo.message}</span>
          <button style={{...btnSmall, padding:"4px 8px"}} onClick={runUndo}>Undo</button>
          <button style={{...btnSmall, padding:"4px 8px", marginLeft:"6px"}} onClick={dismissUndo}>✕</button>
        </div>
      )}

      {/* WEEKLY MENU */}
      <Menu
        menu={menu}
        onGenerate={loadMenu}
        onReroll={rerollDay}
      />

      {/* GROCERY LIST */}
      <GroceryList
        grocery={grocery}
        onGenerate={loadGrocery}
      />

      {/* MENU HISTORY */}
      <History
        history={menuHistory}
        onGenerate={loadHistory}
      />

      {/* CALENDAR VIEW (audit B1): read-only, reuses the /menus fetch */}
      <Calendar menus={menuHistory} onGenerate={loadHistory} />

      {/* INSIGHTS (audit B2): macro overview + deficiency flags + swap suggestions */}
      <Insights data={insights} onGenerate={loadInsights} />

      {/* ADD MEAL */}
      <AddMeal
        name={name}
        ingredients={ingredients}
        category={category}
        categories={categories}
        onNameChange={(e) => setName(e.target.value)}
        onIngredientsChange={(e) => setIngredients(e.target.value)}
        onCategoryChange={(e) => setCategory(e.target.value)}
        onAdd={addMeal}
        onUpload={uploadImage}
      />

      {/* QUICK PICK */}
      <div style={card}>
        <h2>Quick Pick</h2>
        <div style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
          <button style={{...btnSmall, padding:"8px 12px"}} onClick={getTodayMeal}>🍽 Home</button>
          <button style={{...btnSmall, padding:"8px 12px"}} onClick={getTakeout}>🍔 Takeout</button>
        </div>

        {today && (
          <div style={resultBox}>
            <strong>At Home:</strong>
            <h3>{today.name}</h3>
          </div>
        )}

        {takeout && (
          <div style={resultBox}>
            <strong>Takeout:</strong>
            <h3>{takeout.name}</h3>
            <p style={{ opacity: 0.7 }}>{takeout.type}</p>
          </div>
        )}
      </div>

      {/* ALL MEALS (paginated) */}
      <div style={card}>
        <h2>All Meals</h2>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
          <span>Category:</span>
          <select
            style={{ ...input, width: "auto" }}
            value={mealCategory}
            onChange={(e) => { setMealCategory(e.target.value); loadMeals(1); }}
          >
            <option value="">All</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <input
          style={{ ...input, width: "100%" }}
          placeholder="Search meals…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); loadMeals(1); }}  // §5.18
        />

        <ul style={{ listStyle: "none", padding: 0 }}>
          {meals.map((meal) => (
            <li key={meal.id} style={listItem}>
              {editingMeal?.id === meal.id ? (
                <div style={{ display: "block", width: "100%" }}>
                  <input
                    style={input}
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="Meal name"
                  />
                   <input
                     style={input}
                     value={editIngredients}
                     onChange={(e) => setEditIngredients(e.target.value)}
                     placeholder="Ingredients (comma separated)"
                   />
                   <select
                     style={{ ...input, marginBottom: "8px" }}
                     value={editCategory}
                     onChange={(e) => setEditCategory(e.target.value)}
                   >
                     <option value="">(no category)</option>
                     {categories.map((c) => (
                       <option key={c} value={c}>{c}</option>
                     ))}
                   </select>
                   <div style={{ display: "flex", gap: "8px" }}>
                    <button style={btnSmall} onClick={() => saveEdit(meal)}>Save</button>
                    <button style={btnSmall} onClick={cancelEdit}>Cancel</button>
                  </div>
                </div>
              ) : (
                   <>
                     <span>{meal.name}{meal.category ? <span style={{ opacity: 0.6 }}> · {meal.category}</span> : null}</span>
                     <div>
                       <button style={btnSmall} onClick={() => editMeal(meal)}>✏️</button>
                       <button style={btnSmall} onClick={() => deleteMeal(meal)}>❌</button>
                     </div>
                   </>
              )}
            </li>
          ))}
        </ul>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "10px", fontSize: "13px", color: "#9ca3af" }}>
          <span>Page {mealsPage}/{mealsPages} ({mealsTotal} meals)</span>
          <div>
            <button style={btnSmall} onClick={() => loadMeals(mealsPage - 1)} disabled={mealsPage <= 1}>Prev</button>
            <button style={btnSmall} onClick={() => loadMeals(mealsPage + 1)} disabled={mealsPage >= mealsPages}>Next</button>
          </div>
        </div>
      </div>

    </div>
  );
}
