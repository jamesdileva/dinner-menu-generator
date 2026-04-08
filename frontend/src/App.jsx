import { useState } from "react";
import { useEffect } from "react";

export default function App() {
  const [menu, setMenu] = useState(null);
  const [name, setName] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [grocery, setGrocery] = useState(null);
  const [meals, setMeals] = useState([]);

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

      <h2>Add Meal</h2>

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

      <button onClick={addMeal}>Add Meal</button>
      <input type="file" onChange={uploadImage} />  
      <hr />
      <h2>Weekly Menu</h2>
      <button onClick={loadMenu}>Generate Weekly Menu</button>
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

      
      {menu && (
        <ul>
          {Object.entries(menu).map(([day, meal]) => (
            <li key={day}>
              {day}: {meal.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}