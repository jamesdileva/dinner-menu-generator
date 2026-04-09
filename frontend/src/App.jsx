import { useState } from "react";
import { useEffect } from "react";

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

const btnSmall = {
  ...btn,
  padding: "4px 8px",
  marginLeft: "5px"
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
export default function App() {
  const [menu, setMenu] = useState(null);
  const [name, setName] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [grocery, setGrocery] = useState(null);
  const [meals, setMeals] = useState([]);
  const [today, setToday] = useState(null);
  const [takeout, setTakeout] = useState(null);

  async function getTodayMeal() {
    const res = await fetch("http://localhost:5000/menu/today");
    const data = await res.json();
    setToday(data);
  }
  async function loadMenu() {
    const res = await fetch("http://localhost:5000/menu/week");
    const data = await res.json();
    setMenu(data);
  }

async function loadMeals() {
  const res = await fetch("http://localhost:5000/meals");
  const data = await res.json();
  setMeals(data);
}

  async function loadMenu() {
    const res = await fetch("http://localhost:5000/menu/week");
    const data = await res.json();
    setMenu(data);
    setGrocery(null); // reset grocery
  }

async function loadGrocery() {
  const res = await fetch("http://localhost:5000/grocery");
  const data = await res.json();

  if (data.error) {
    alert(data.error);
    return;
  }

  setGrocery(data);
}

async function getTakeout() {
  const res = await fetch("http://localhost:5000/menu/takeout");
  const data = await res.json();
  setTakeout(data);
}

async function rerollDay(day) {
  const res = await fetch(`http://localhost:5000/menu/reroll/${day}`, {
    method: "POST"
  });

  const data = await res.json();

  setMenu(prev => ({
    ...prev,
    [day]: data.meal
  }));
}

async function editMeal(meal) {
  const newName = prompt("New name:", meal.name);
  if (!newName) return;

  const newIngredients = prompt(
    "Ingredients (comma separated):",
    meal.ingredients.join(", ")
  );

  if (!newIngredients) return;

  await fetch(`http://localhost:5000/meal/${meal.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: newName,
      ingredients: newIngredients.split(",").map(i => i.trim())
    })
  });

  loadMeals();
}

async function uploadImage(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("image", file);

  const res = await fetch("http://localhost:5000/upload-menu", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  console.log(data);

  alert(
    `Added: ${data.added.length}
  Updated: ${data.updated.length}
  Skipped: ${data.skipped.length}`
  );

  loadMeals(); // 🔥 refresh UI
}

async function deleteMeal(id) {
  await fetch(`http://localhost:5000/meal/${id}`, {
    method: "DELETE"
  });

  loadMeals(); // ✅ refresh UI
}

  async function addMeal() {
  const res = await fetch("http://localhost:5000/meal", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name,
      ingredients: ingredients.split(",").map(i => i.trim())
    })
  });

  const data = await res.json();

  if (data.error) {
    alert(data.error);
    return;
  }

  setName("");
  setIngredients("");

  loadMeals(); // ✅ THIS FIXES IT
}
useEffect(() => {
  loadMeals();
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
    <h1 style={{ marginBottom: "25px" }}>🍽 Dinner Planner</h1>

    {/* WEEKLY MENU */}
    <div style={card}>
      <h2>Weekly Menu</h2>
      <button style={btn} onClick={loadMenu}>Generate Week</button>

      {menu && (
        <ul style={{ listStyle: "none", padding: 0, marginTop: "10px" }}>
          {Object.entries(menu).map(([day, meal]) => (
            <li key={day} style={listItem}>
              <span><strong>{day}:</strong> {meal.name}</span>
              <button style={btnSmall} onClick={() => rerollDay(day)}>🔄</button>
            </li>
          ))}
        </ul>
      )}
    </div>

    {/* GROCERY LIST */}
    <div style={card}>
      <h2>Grocery List</h2>
      <button style={btn} onClick={loadGrocery}>Generate Grocery</button>

      {grocery && (
        <div style={{ marginTop: "15px" }}>
          {Object.entries(grocery).map(([category, items]) => (
            <div key={category} style={{ marginBottom: "15px" }}>
              <h3 style={{ color: "#9ca3af" }}>{category}</h3>
              <ul style={{ paddingLeft: "15px" }}>
                {items.map((i) => (
                  <li key={i.item}>
                    {i.item} <span style={{ opacity: 0.6 }}>x{i.qty}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>

    {/* ADD MEAL */}
    <div style={card}>
      <h2>Add Meal</h2>
      <input
        style={input}
        placeholder="Meal name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <input
        style={input}
        placeholder="Ingredients (comma separated)"
        value={ingredients}
        onChange={(e) => setIngredients(e.target.value)}
      />

      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <button style={btn} onClick={addMeal}>Add Meal</button>
        <input type="file" onChange={uploadImage} />
      </div>
    </div>

    {/* QUICK PICK */}
    <div style={card}>
      <h2>Quick Pick</h2>
      <div style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
        <button style={btn} onClick={getTodayMeal}>🍽 Home</button>
        <button style={btn} onClick={getTakeout}>🍔 Takeout</button>
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

    {/* ALL MEALS */}
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
    </div>

  </div>
);
}