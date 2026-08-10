import { useState, useEffect, useRef } from "react";
import { apiFetch, MEALS_PER_PAGE } from "./api.js";
import Menu from "./components/Menu.jsx";
import GroceryList from "./components/GroceryList.jsx";
import ManageMeals from "./components/ManageMeals.jsx";
import QuickPickBadge from "./components/QuickPickBadge.jsx";
import Modal from "./components/Modal.jsx";
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
  const [menuHistory, setMenuHistory] = useState(null);
  const [insights, setInsights] = useState(null);
  const [activeHistoryTab, setActiveHistoryTab] = useState("list");

  const [meals, setMeals] = useState([]);
  const [mealsPage, setMealsPage] = useState(1);
  const [mealsPages, setMealsPages] = useState(1);
  const [mealsTotal, setMealsTotal] = useState(0);
  const [mealCategory, setMealCategory] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // §5.12 inline edit + undo
  const [editingMeal, setEditingMeal] = useState(null);
  const [editName, setEditName] = useState("");
  const [editIngredients, setEditIngredients] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [undo, setUndo] = useState(null);
  const undoTimer = useRef(null);

  // §5.14 categories
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("");

  // §13.21 header badges
  const [addMealModalOpen, setAddMealModalOpen] = useState(false);
  const [quickPickResult, setQuickPickResult] = useState(null);

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
    const data = await apiFetch("/menu/today");
    setQuickPickResult({ mode: "home", meal: data });
  });

  const getTakeout = () => withLoading(async () => {
    const data = await apiFetch("/menu/takeout");
    setQuickPickResult({ mode: "takeout", meal: data });
  });

  const loadMenu = () => withLoading(async () => {
    const data = await apiFetch("/menu/week");
    setMenu(data);
    setGrocery(null);
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

  // §13.23: load saved groceries for the tabs
  const loadSavings = () =>
    apiFetch("/savings").then((r) => setSavings(r.savings || [])).catch(() => {});
  const [savings, setSavings] = useState([]);

  useEffect(() => {
    loadSavings();
  }, []);

  const addFromSavings = (itemName) => {
    apiFetch("/saving", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: itemName }),
    }).catch(() => {});
  };

  const deleteSaving = (id) => {
    apiFetch(`/saving/${id}`, { method: "DELETE" })
      .then(() => loadSavings())
      .catch(() => {});
  };

  const rerollDay = async (day) => {
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

  const loadMeals = (page = 1, categoryFilter = null, searchQuery = null) =>
    withLoading(async () => {
      let url = `/meals?page=${page}&limit=${MEALS_PER_PAGE}`;
      if (categoryFilter !== null) setMealCategory(categoryFilter);
      if (searchQuery !== null) setSearch(searchQuery);
      if (categoryFilter !== null && categoryFilter !== "") {
        url += `&category=${encodeURIComponent(categoryFilter)}`;
      }
      if (searchQuery !== null && searchQuery !== "") {
        url += `&search=${encodeURIComponent(searchQuery)}`;
      }
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
          category: editCategory || undefined,
        }),
      });
      cancelEdit();
      loadMeals(mealsPage, mealCategory, search);
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
      loadMeals(1, mealCategory, search);
      if (addMealModalOpen) setAddMealModalOpen(false);
    });
  };

  const deleteMeal = (meal) =>
    withLoading(async () => {
      await apiFetch(`/meal/${meal.id}`, { method: "DELETE" });
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
          .then(() => loadMeals(mealsPage, mealCategory, search))
          .catch(() => {})
      );
      loadMeals(mealsPage, mealCategory, search);
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
          category: category || undefined,
        }),
      });
      setName("");
      setIngredients("");
      setCategory("");
      setAddMealModalOpen(false);
      loadMeals(1, mealCategory, search);
    });

  // §6.14 Escape cancels edit or modal, dismisses undo
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") {
        if (editingMeal) {
          cancelEdit();
        } else if (undo) {
          dismissUndo();
        } else if (addMealModalOpen) {
          setAddMealModalOpen(false);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [editingMeal, undo, addMealModalOpen]);

  useEffect(() => {
    loadMeals();
    loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onCategoryFilter = (e) => loadMeals(1, e.target.value, search);
  const onSearch = (e) => loadMeals(1, mealCategory, e.target.value);

  return (
    <div className="app-shell">
      {/* Header with badge buttons */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h1 style={{ margin: 0 }}>Dinner Planner</h1>
          <button
            className="btn-sm"
            style={{ padding: "4px 10px", fontSize: "13px" }}
            onClick={() => setAddMealModalOpen(true)}
            title="Add a new meal"
          >
            ＋ Add Meal
          </button>
          <QuickPickBadge
            onPickHome={getTodayMeal}
            onPickTakeout={getTakeout}
            result={quickPickResult}
          />
        </div>
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
            ×
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
            ×
          </button>
        </div>
      )}

      {/* All Meals card (with Meals/Snacks/Staples tabs) */}
      <ManageMeals
        meals={meals}
        mealsPage={mealsPage}
        mealsPages={mealsPages}
        mealsTotal={mealsTotal}
        categories={categories}
        editingMeal={editingMeal}
        editName={editName}
        editIngredients={editIngredients}
        editCategory={editCategory}
        onEditNameChange={(e) => setEditName(e.target.value)}
        onEditIngredientsChange={(e) => setEditIngredients(e.target.value)}
        onEditCategoryChange={(e) => setEditCategory(e.target.value)}
        onEditMeal={editMeal}
        onCancelEdit={cancelEdit}
        onSaveEdit={saveEdit}
        onDeleteMeal={deleteMeal}
        onPageChange={loadMeals}
        onCategoryFilter={onCategoryFilter}
        onSearch={onSearch}
        savings={savings}
        onAddFromSavings={addFromSavings}
        onDeleteSaving={deleteSaving}
      />

      {/* Weekly Menu + Grocery List (side-by-side on desktop, stacked on mobile) */}
      <div className="main-grid">
        <Menu menu={menu} onGenerate={loadMenu} onReroll={rerollDay} />
        <GroceryList grocery={grocery} onGenerate={loadGrocery} />
      </div>

      {/* Past Menus + Insights (secondary, side-by-side on desktop) */}
      <div className="secondary-grid">
        {/* Past Menus */}
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

        {/* Insights */}
        <Insights data={insights} onGenerate={loadInsights} />
      </div>

      {/* Add Meal Modal (§13.21) */}
      <Modal
        title="Add Meal"
        open={addMealModalOpen}
        onClose={() => setAddMealModalOpen(false)}
      >
        <input
          className="input-field"
          placeholder="Meal name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addMeal()}
          autoFocus
        />
        <select className="input-field" value={category || ""} onChange={(e) => setCategory(e.target.value)}>
          <option value="">(no category)</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <input
          className="input-field"
          placeholder="Ingredients (comma separated)"
          value={ingredients}
          onChange={(e) => setIngredients(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addMeal()}
        />
        <div className="row-gap" style={{ gap: "10px" }}>
          <button className="btn" onClick={addMeal}>
            Add Meal
          </button>
          <input type="file" onChange={uploadImage} />
        </div>
      </Modal>
    </div>
  );
}
