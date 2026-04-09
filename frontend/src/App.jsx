import { useState } from "react";
import { useEffect } from "react";

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
    <div style={{ padding: "1rem" }}>
      <h1>Dinner Planner</h1>



      <h2>All Meals</h2>

      <ul>
        {meals.map((meal) => (
          <li key={meal.id}>
            {meal.name}
            <button onClick={() => deleteMeal(meal.id)}>❌</button>
            <button onClick={() => editMeal(meal)}>✏️</button>
          </li>
        ))}
      </ul>
      

      <input
        placeholder="Meal name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <input
        placeholder="Ingredients (comma separated)"
        value={ingredients}
        onChange={(e) => setIngredients(e.target.value)}
      />
            <h2>Add Meal</h2>
      <button onClick={addMeal}>Add Meal</button>
      <input type="file" onChange={uploadImage} />  
      <hr />
    
        <hr />

      <h2>Quick Pick</h2>

      <button onClick={getTodayMeal}>
        🍽 What should I eat tonight?
      </button>

      <button onClick={getTakeout}>
        🍔 Or just eat out
      </button>

      {today && (
        <div>
          <h3>Eat at Home:</h3>
          <h2>{today.name}</h2>
        </div>
      )}

      {takeout && (
        <div>
          <h3>Eat Out:</h3>
          <h2>{takeout.name}</h2>
          <p>{takeout.type}</p>
        </div>
      )}

      <button onClick={loadGrocery}>Generate Grocery List</button>
      {grocery && (
  <>
          <h2>Grocery List</h2>

          {Object.entries(grocery).map(([category, items]) => (
            <div key={category}>
              <h3>{category}</h3>
              <ul>
                {items.map((i) => (
                  <li key={i.item}>
                    {i.item}: {i.qty}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </>
      )}

      <h2>Weekly Menu</h2>
      <button onClick={loadMenu}>Generate Weekly Menu</button>
      {menu && (
        <ul>
          {Object.entries(menu).map(([day, meal]) => (
            <li key={day}>
              {day}: {meal.name}
              <button onClick={() => rerollDay(day)}>🔄</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}