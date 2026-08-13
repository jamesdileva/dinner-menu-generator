import { useState, useEffect, useRef } from "react";
import { apiFetch, MEALS_PER_PAGE } from "./api.js";
import Menu from "./components/Menu.jsx";
import GroceryList from "./components/GroceryList.jsx";
import ManageMeals from "./components/ManageMeals.jsx";
import QuickPickBadge from "./components/QuickPickBadge.jsx";
import Modal from "./components/Modal.jsx";
import SuggestMealModal from "./components/SuggestMealModal.jsx";
import History from "./components/History.jsx";
import Calendar from "./components/Calendar.jsx";
import Insights from "./components/Insights.jsx";

const UNDO_WINDOW_MS = 6000;
const PAGE_SIZE_OPTIONS = [5, 10, 15, 20];

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

  // §13.21b — configurable page size (default 5, persisted to localStorage)
  const [mealsPerPage, setMealsPerPage] = useState(() => {
    const saved = localStorage.getItem("mealsPerPage");
    return saved ? parseInt(saved, 10) : MEALS_PER_PAGE;
  });

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

  // §13.3b — add snack / add staple badges (modal with single name input)
  const [addGroceryModalOpen, setAddGroceryModalOpen] = useState(false);
  const [addGroceryGroup, setAddGroceryGroup] = useState("snacks");
  const [addGroceryName, setAddGroceryName] = useState("");

  // §16 — Ollama / local LLM settings + AI feature state
  const [ollamaEnabled, setOllamaEnabled] = useState(() => {
    const saved = localStorage.getItem("ollamaEnabled");
    return saved === "true";
  });
  const [settings, setSettings] = useState(null);
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [suggestMealModalOpen, setSuggestMealModalOpen] = useState(false);
  const [enhancingGrocery, setEnhancingGrocery] = useState(false);
  const [enhancedGrocery, setEnhancedGrocery] = useState(null);

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

  // §5.20 — browser close detection: send a beacon to /shutdown so the
  // PyInstaller exe can exit when the user closes the tab/window.
  useEffect(() => {
    const handleUnload = () => {
      navigator.sendBeacon("/shutdown");
    };
    window.addEventListener("beforeunload", handleUnload);
    return () => window.removeEventListener("beforeunload", handleUnload);
  }, []);

  const getTodayMeal = () => withLoading(async () => {
    const data = await apiFetch("/menu/today");
    setQuickPickResult({ mode: "home", meal: data });
  });

  const getTakeout = () => withLoading(async () => {
    const data = await apiFetch("/menu/takeout");
    setQuickPickResult({ mode: "takeout", meal: data });
  });

  // §13a.2 — load the current week's menu if one exists; fall back to generating a new one.
  const loadMenu = () => withLoading(async () => {
    const last = await apiFetch("/menu/last");
    if (last.menu) {
      setMenu(last.menu);
    } else {
      setMenu(await apiFetch("/menu/week"));
    }
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

  // §16 — settings + AI handlers
  const loadSettings = () =>
    apiFetch("/settings")
      .then((r) => setSettings(r))
      .catch(() => setSettings(null));

  const toggleOllama = () => {
    const next = !ollamaEnabled;
    setOllamaEnabled(next);
    localStorage.setItem("ollamaEnabled", String(next));
    apiFetch("/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ use_ollama: next }),
    }).catch(() => {});
  };

  const enhanceGrocery = () =>
    withLoading(async () => {
      setEnhancingGrocery(true);
      try {
        const r = await apiFetch("/grocery/enhance");
        setEnhancedGrocery(r);
      } catch (e) {
        setError(e.message);
      } finally {
        setEnhancingGrocery(false);
      }
    });

  const loadAiSuggestions = () =>
    withLoading(async () => {
      const prefs = "";
      const r = await apiFetch(`/menu/suggest${prefs ? `?preferences=${encodeURIComponent(prefs)}` : ""}`);
      setAiSuggestions(r.suggestions || []);
    });

  // §16.4 — save AI-suggested meal to the database
  const saveAiMeal = (suggestion) =>
    withLoading(async () => {
      await apiFetch("/meal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: suggestion.name,
          ingredients: suggestion.ingredients,
          category: "AI Suggested",
        }),
      });
      setSuggestMealModalOpen(false);
      setAiSuggestions(null);
      loadMeals(1, mealCategory, search);
    });

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
      let url = `/meals?page=${page}&limit=${mealsPerPage}`;
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

  const onPerPageChange = (e) => {
    const val = parseInt(e.target.value, 10);
    setMealsPerPage(val);
    localStorage.setItem("mealsPerPage", val);
    loadMeals(1, mealCategory, search);
  };

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

  // §13.3b — add a snack or staple to the saved-grocery catalog
  const addGrocery = () =>
    withLoading(async () => {
      await apiFetch("/saving", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: addGroceryName.trim(),
          group: addGroceryGroup,
        }),
      });
      setAddGroceryName("");
      setAddGroceryModalOpen(false);
      loadSavings();
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
        } else if (addGroceryModalOpen) {
          setAddGroceryModalOpen(false);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [editingMeal, undo, addMealModalOpen, addGroceryModalOpen]);

  useEffect(() => {
    loadMeals();
    loadCategories();
    // §13a.2 — resume last week's menu if present, then load the grocery list
    loadMenu();
    loadGrocery();
    // §16 — fetch Ollama settings
    loadSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onCategoryFilter = (e) => loadMeals(1, e.target.value, search);
  const onSearch = (e) => loadMeals(1, mealCategory, e.target.value);

  return (
    <div className="app-shell">
      {/* Header with badge buttons (§13.21b — sticky on scroll) */}
      <div className="app-header">
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
          <button
            className="btn-sm"
            style={{ padding: "4px 10px", fontSize: "13px" }}
            onClick={() => { setAddGroceryGroup("snacks"); setAddGroceryModalOpen(true); }}
            title="Add a snack to the saved grocery catalog"
          >
            ＋ Add Snack
          </button>
          <button
            className="btn-sm"
            style={{ padding: "4px 10px", fontSize: "13px" }}
            onClick={() => { setAddGroceryGroup("staples"); setAddGroceryModalOpen(true); }}
            title="Add a staple to the saved grocery catalog"
          >
            ＋ Add Staple
          </button>
          <QuickPickBadge
            onPickHome={getTodayMeal}
            onPickTakeout={getTakeout}
            result={quickPickResult}
          />
          <button
            className="btn-sm"
            style={{ padding: "4px 10px", fontSize: "13px" }}
            onClick={() => setSuggestMealModalOpen(true)}
            title="AI suggests a meal (requires Ollama)"
          >
            💡 Suggest Meal
          </button>
        </div>
        <div className="row-gap" style={{ gap: "8px" }}>
          <button
            className="btn-sm"
            style={{
              padding: "4px 10px",
              fontSize: "13px",
              background: ollamaEnabled ? "var(--accent)" : "var(--bg-panel)",
              color: ollamaEnabled ? "#fff" : "var(--text-muted)",
            }}
            onClick={toggleOllama}
            title={
              ollamaEnabled
                ? settings?.ollama_available
                  ? `AI enabled (model: ${settings?.ollama_model || "llama3.1:8b"})`
                  : "AI enabled but Ollama not running"
                : "AI features OFF"
            }
          >
            {ollamaEnabled ? "🧠 AI On" : "🧠 AI Off"}
          </button>
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
        mealsPerPage={mealsPerPage}
        onPerPageChange={onPerPageChange}
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
        <GroceryList
          grocery={grocery}
          onGenerate={loadGrocery}
          savings={savings}
          onSavingsChange={loadSavings}
          ollamaEnabled={ollamaEnabled}
          enhancedGrocery={enhancedGrocery}
          onEnhance={enhanceGrocery}
          enhancing={enhancingGrocery}
        />
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
        <Insights
          data={insights}
          onGenerate={loadInsights}
          ollamaEnabled={ollamaEnabled}
        />
      </div>

      {/* §16.4 — AI meal suggestion modal */}
      <SuggestMealModal
        open={suggestMealModalOpen}
        onClose={() => setSuggestMealModalOpen(false)}
        suggestions={aiSuggestions}
        onSuggest={loadAiSuggestions}
        loading={loading}
        onSave={saveAiMeal}
        ollamaEnabled={ollamaEnabled}
      />
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

      {/* §13.3b — Add Snack / Add Staple modal */}
      <Modal
        title={`Add ${addGroceryGroup === "snacks" ? "Snack" : "Staple"}`}
        open={addGroceryModalOpen}
        onClose={() => setAddGroceryModalOpen(false)}
      >
        <input
          className="input-field"
          placeholder={addGroceryGroup === "snacks" ? "Snack name…" : "Staple name…"}
          value={addGroceryName}
          onChange={(e) => setAddGroceryName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addGrocery()}
          autoFocus
        />
        <div className="row-gap" style={{ gap: "10px", marginTop: "10px" }}>
          <button className="btn" onClick={addGrocery}>
            Add
          </button>
          <button className="btn-sm" onClick={() => setAddGroceryModalOpen(false)}>
            Cancel
          </button>
        </div>
      </Modal>
    </div>
  );
}
