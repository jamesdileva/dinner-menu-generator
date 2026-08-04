import { useState, useEffect } from "react";
import { apiFetch, MEALS_PER_PAGE } from "./api.js";
import Menu from "./components/Menu.jsx";
import GroceryList from "./components/GroceryList.jsx";
import AddMeal from "./components/AddMeal.jsx";

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

export default function App() {
  const [menu, setMenu] = useState(null);
  const [name, setName] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [grocery, setGrocery] = useState(null);
  const [meals, setMeals] = useState([]);
  const [mealsPage, setMealsPage] = useState(1);
  const [mealsPages, setMealsPages] = useState(1);
  const [mealsTotal, setMealsTotal] = useState(0);
  const [today, setToday] = useState(null);
  const [takeout, setTakeout] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  const rerollDay = (day) => withLoading(async () => {
    const data = await apiFetch(`/menu/reroll/${day}`, { method: "POST" });
    setMenu(prev => ({
      ...prev,
      [day]: data.meal
    }));
  });

  const loadMeals = (page = 1) => withLoading(async () => {
    const data = await apiFetch(`/meals?page=${page}&limit=${MEALS_PER_PAGE}`);
    setMeals(data.meals);
    setMealsPage(data.page);
    setMealsPages(data.pages);
    setMealsTotal(data.total);
  });

  const editMeal = (meal) => {
    const newName = prompt("New name:", meal.name);
    if (!newName) return;

    const newIngredients = prompt(
      "Ingredients (comma separated):",
      meal.ingredients.join(", ")
    );

    if (!newIngredients) return;

    withLoading(async () => {
      await apiFetch(`/meal/${meal.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newName,
          ingredients: newIngredients.split(",").map(i => i.trim())
        })
      });
      loadMeals(mealsPage);
    });
  };

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

  const deleteMeal = (id) => withLoading(async () => {
    await apiFetch(`/meal/${id}`, { method: "DELETE" });
    loadMeals(mealsPage);
  });

  const addMeal = () => withLoading(async () => {
    await apiFetch("/meal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        ingredients: ingredients.split(",").map(i => i.trim())
      })
    });
    setName("");
    setIngredients("");
    loadMeals(1);
  });

  useEffect(() => {
    loadMeals();
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

      {/* ADD MEAL */}
      <AddMeal
        name={name}
        ingredients={ingredients}
        onNameChange={(e) => setName(e.target.value)}
        onIngredientsChange={(e) => setIngredients(e.target.value)}
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
        <ul style={{ listStyle: "none", padding: 0 }}>
          {meals.map((meal) => (
            <li key={meal.id} style={listItem}>
              <span>{meal.name}</span>
              <div>
                <button style={btnSmall} onClick={() => editMeal(meal)}>✏️</button>
                <button style={btnSmall} onClick={() => deleteMeal(meal.id)}>❌</button>
              </div>
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
