import { useState, useEffect, useRef } from "react";
import { apiFetch, MEALS_PER_PAGE } from "./api.js";
import Menu from "./components/Menu.jsx";
import GroceryList from "./components/GroceryList.jsx";
import AddMeal from "./components/AddMeal.jsx";
import History from "./components/History.jsx";
import Calendar from "./components/Calendar.jsx";
import Insights from "./components/Insights.jsx";

const UNDO_WINDOW_MS = 6000;

function setTheme(theme) {
  localStorage.setItem("theme", theme);
  const root = document.getElementById("root");
  root.setAttribute("data-theme", theme);
}

function toggleTheme() {
  const root = document.getElementById("root");
  const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  setTheme(next);
}

export default function App() {
  const [menu, setMenu] = useState(null);
  const [name, setName] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [grocery, setGrocery] = useState(null);
  const [menuHistory, setMenuHistory] = useState(null); // §5.15
  const [insights, setInsights] = useState(null); // audit B2
  const [activeHistoryTab, setActiveHistoryTab] = useState("list"); // §13a.6

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
  const [search, setSearch] = useState(""); // §5.18 meal name search

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
    return () => {
      if (undoTimer.current) clearTimeout(undoTimer.current);
    };
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
      setMenu((prev) => ({ ...prev, [day]: data.meal }));
      if (prevMeal) {
        showUndo(`Rolled "${prevMeal.name}" for ${day}; undo?`, () =>
          apiFetch(`/menu/${day}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(prevMeal),
          })
            .then((res) =>
              setMenu((p) => ({ ...p, [day]: res.meal ?? prevMeal }))
            )
            .catch(() => {})
        );
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const loadMeals = (page = 1) =>
    withLoading(async () => {
      let url = `/meals?page=${page}&limit=${MEALS_PER_PAGE}`;
      if (mealCategory) url += `&category=${encodeURIComponent(mealCategory)}`; // §5.14
      if (search) url += `&search=${encodeURIComponent(search)}`; // §5.18
      const data = await apiFetch(url);
      setMeals(data.meals);
      setMealsPage(data.page);
      setMealsPages(data.pages);
      setMealsTotal(data.total);
    });

  const loadCategories = () => {
    apiFetch("/meals/categories")
      .then((res) => setCategories(res.categories))
      .catch(() => {});
  };

  const editMeal = (meal) => {
    setEditingMeal(meal);
    setEditName(meal.name);
    setEditIngredients(
      Array.isArray(meal.ingredients) ? meal.ingredients.join(", ") : ""
    );
    setEditCategory(meal.category || "");
  };

  const cancelEdit = () => {
    setEditingMeal(null);
    setEditName("");
    setEditIngredients("");
    setEditCategory("");
  };

  const saveEdit = (meal) =>
    withLoading(async () => {
      await apiFetch(`/meal/${meal.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: editName.trim(),
          ingredients: editIngredients
            .split(",")
            .map((i) => i.trim())
            .filter(Boolean),
          category: editCategory || undefined, // §5.14
        }),
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
        body: formData,
      });
      alert(
        `Added: ${data.added.length}\nUpdated: ${data.updated.length}\nSkipped: ${data.skipped.length}`
      );
      loadMeals(1);
    });
  };

  const deleteMeal = (meal) =>
    withLoading(async () => {
      await apiFetch(`/meal/${meal.id}`, { method: "DELETE" });
      // §5.12: offer Undo; recreating needs the original meal object
      showUndo(`Deleted "${meal.name}"; undo?`, () =>
        apiFetch("/meal", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            id: meal.id,
            name: meal.name,
            ingredients: meal.ingredients,
          }),
        })
          .then(() => loadMeals(mealsPage))
          .catch(() => {})
      );
      loadMeals(mealsPage);
    });

  const addMeal = () =>
    withLoading(async () => {
      await apiFetch("/meal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          ingredients: ingredients
            .split(",")
            .map((i) => i.trim())
            .filter(Boolean),
          category: category || undefined, // §5.14
        }),
      });
      setName("");
      setIngredients("");
      setCategory("");
      loadMeals(1);
    });

  useEffect(() => {
    loadMeals();
    loadCategories(); // §5.14
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="app-shell">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <h1 style={{ margin: 0 }}>Dinner Planner</h1>
        <button
          className="btn-sm"
          style={{ padding: "4px 10px", fontSize: "13px" }}
          onClick={toggleTheme}
          title="Toggle dark / light"
        >
          {document.getElementById("root")?.getAttribute("data-theme") === "dark" ? "☀️ Light" : "🌙 Dark"}
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button className="btn-sm" onClick={() => setError(null)}>
            ✕
          </button>
        </div>
      )}
      {loading && (
        <div className="row-gap" style={{ marginBottom: "10px" }}>
          <span>Loading</span>
          <span className="spinner"></span>
        </div>
      )}

      {undo && (
        <div className="undo-bar">
          <span>{undo.message}</span>
          <button className="btn-sm" onClick={runUndo}>
            Undo
          </button>
          <button className="btn-sm" style={{ marginLeft: "6px" }} onClick={dismissUndo}>
            ✕
          </button>
        </div>
      )}

      {/* WEEKLY MENU */}
      <Menu menu={menu} onGenerate={loadMenu} onReroll={rerollDay} />

      {/* GROCERY LIST */}
      <GroceryList grocery={grocery} onGenerate={loadGrocery} />

      {/* QUICK PICK */}
      <div className="card">
        <h2>Quick Pick</h2>
        <div className="row-wrap" style={{ gap: "10px", marginBottom: "10px" }}>
          <button className="btn" onClick={getTodayMeal}>
            Home
          </button>
          <button className="btn" onClick={getTakeout}>
            Takeout
          </button>
        </div>

        {today && (
          <div className="result-box">
            <strong>At Home:</strong>
            <h3 style={{ margin: "4px 0 0" }}>{today.name}</h3>
          </div>
        )}

        {takeout && (
          <div className="result-box">
            <strong>Takeout:</strong>
            <h3 style={{ margin: "4px 0 0" }}>{takeout.name}</h3>
            <p style={{ opacity: 0.7 }}>{takeout.type}</p>
          </div>
        )}
      </div>

      {/* PAST MENUS (history / calendar tabs) — §13a.6 */}
      <div className="card">
        <h2>Past Menus</h2>
        <div className="row-gap" style={{ marginBottom: "10px" }}>
          <button
            className="btn-sm"
            style={{
              background: activeHistoryTab === "list" ? "var(--accent)" : "var(--bg-panel)",
              color: activeHistoryTab === "list" ? "#fff" : "var(--text-muted)",
            }}
            onClick={() => setActiveHistoryTab("list")}
          >
            List
          </button>
          <button
            className="btn-sm"
            style={{
              background: activeHistoryTab === "calendar" ? "var(--accent)" : "var(--bg-panel)",
              color: activeHistoryTab === "calendar" ? "#fff" : "var(--text-muted)",
            }}
            onClick={() => setActiveHistoryTab("calendar")}
          >
            Calendar
          </button>
        </div>

        {activeHistoryTab === "list" && (
          <History history={menuHistory} onGenerate={loadHistory} />
        )}
        {activeHistoryTab === "calendar" && (
          <Calendar menus={menuHistory} onGenerate={loadHistory} />
        )}

        {menuHistory === null && (
          <button className="btn" onClick={loadHistory}>
            Load History
          </button>
        )}
      </div>

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

      {/* ALL MEALS (paginated) */}
      <div className="card">
        <h2>All Meals</h2>
        <div className="row-gap" style={{ marginBottom: "10px" }}>
          <span>Category:</span>
          <select
            className="input-field-sm"
            value={mealCategory}
            onChange={(e) => {
              setMealCategory(e.target.value);
              loadMeals(1);
            }}
          >
            <option value="">All</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <input
          className="input-field"
          placeholder="Search meals…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            loadMeals(1);
          }}
        />

        <ul style={{ listStyle: "none", padding: 0 }}>
          {meals.map((meal) => (
            <li key={meal.id} className="list-item">
              {editingMeal?.id === meal.id ? (
                <div style={{ display: "block", width: "100%" }}>
                  <input
                    className="input-field"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="Meal name"
                  />
                  <input
                    className="input-field"
                    value={editIngredients}
                    onChange={(e) => setEditIngredients(e.target.value)}
                    placeholder="Ingredients (comma separated)"
                  />
                  <select
                    className="input-field"
                    style={{ marginBottom: "8px" }}
                    value={editCategory}
                    onChange={(e) => setEditCategory(e.target.value)}
                  >
                    <option value="">(no category)</option>
                    {categories.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <div className="row-gap" style={{ gap: "8px" }}>
                    <button className="btn-sm" onClick={() => saveEdit(meal)}>
                      Save
                    </button>
                    <button className="btn-sm" onClick={cancelEdit}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <span>
                    {meal.name}
                    {meal.category ? (
                      <span className="category-chip">{meal.category}</span>
                    ) : null}
                  </span>
                  <div>
                    <button className="btn-sm" onClick={() => editMeal(meal)}>
                      Edit
                    </button>
                    <button className="btn-sm" onClick={() => deleteMeal(meal)}>
                      Delete
                    </button>
                  </div>
                </>
              )}
            </li>
          ))}
        </ul>

        <div
          className="row-between"
          style={{ marginTop: "10px", fontSize: "13px", color: "var(--text-muted)" }}
        >
          <span>
            Page {mealsPage}/{mealsPages} ({mealsTotal} meals)
          </span>
          <div className="row-gap" style={{ gap: "6px" }}>
            <button
              className="btn-sm"
              onClick={() => loadMeals(mealsPage - 1)}
              disabled={mealsPage <= 1}
            >
              Prev
            </button>
            <button
              className="btn-sm"
              onClick={() => loadMeals(mealsPage + 1)}
              disabled={mealsPage >= mealsPages}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
