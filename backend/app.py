from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import random
from PIL import Image
import pytesseract
import json

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


global current_week
current_week = []
app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:123@127.0.0.1:5432/dinner_app"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



db = SQLAlchemy(app)

# ✅ MODEL FIRST
class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ingredients = db.Column(db.JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients
        }

class WeeklyMenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meals = db.Column(db.JSON)       

def generate_ingredients(meal_name):
    name = meal_name.lower()

    if "taco" in name:
        return ["beef", "tortilla", "cheese"]
    if "pizza" in name:
        return ["dough", "cheese", "tomato sauce"]
    if "alfredo" in name:
        return ["chicken", "pasta", "cream"]
    if "salad" in name:
        return ["lettuce", "tomato", "dressing"]
    if "burger" in name:
        return ["beef", "bun", "lettuce"]
    if "rice" in name:
        return ["rice", "soy sauce", "egg"]
    if "shrimp" in name:
        return ["shrimp", "garlic", "butter"]

    # fallback
    return ["ingredient1", "ingredient2"]

def categorize_ingredient(item):
    item = item.lower()

    if item in ["chicken", "beef", "pork", "shrimp", "egg"]:
        return "Protein"
    if item in ["lettuce", "tomato", "onion", "garlic"]:
        return "Produce"
    if item in ["milk", "cheese", "butter", "cream"]:
        return "Dairy"
    if item in ["rice", "pasta", "bread", "bun", "tortilla"]:
        return "Grains"
    
    return "Other"

import json

def enhance_grocery_list(grocery):
    prompt = f"""
    Convert this grocery list into realistic shopping quantities.

    Return ONLY valid JSON in this format:
    {{
      "Protein": [{{"item": "...", "qty": "..."}}, ...]
    }}

    Data:
    {grocery}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return jsonify(json.loads(response.choices[0].message.content))


# ✅ ROUTES
@app.route("/")
def home():
    return "API running"
    
@app.route("/init-db")
def init_db():
    db.create_all()
    return "DB initialized"

@app.route("/upload-menu", methods=["POST"])
def upload_menu():
    try:
        file = request.files["image"]
        image = Image.open(file)

        text = pytesseract.image_to_string(image)

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        cleaned_meals = []

        for line in lines:
            # ❌ Remove junk
            if len(line) < 3:
                continue
            if "weekly" in line.lower():
                continue

            # ✅ Fix common OCR issues
            line = line.replace("e ", "")  # removes "e Chicken"
            line = line.replace(" - ", "-")
            line = line.strip()

            cleaned_meals.append(line)

        added = []
        skipped = []
        updated = []
        for meal_name in cleaned_meals:
            name_lower = meal_name.lower()

            existing = Meal.query.filter(
                db.func.lower(Meal.name) == name_lower
            ).first()

            if existing:
                # 🔥 NEW LOGIC: fill missing ingredients
                if not existing.ingredients or len(existing.ingredients) == 0:
                    existing.ingredients = generate_ingredients(meal_name)
                    updated.append(meal_name)
                else:
                    skipped.append(meal_name)
                continue

            meal = Meal(
                name=meal_name,
                ingredients=generate_ingredients(meal_name)  # we’ll upgrade this later
            )

            db.session.add(meal)
            added.append(meal_name)

        db.session.commit()

        return jsonify({
            "added": added,
            "updated": updated,
            "skipped": skipped
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/meal", methods=["POST"])
def add_meal():
    data = request.json
    name = data["name"].strip().lower()

    # ✅ Check for duplicate
    existing = Meal.query.filter(
        db.func.lower(Meal.name) == name
    ).first()

    if existing:
        return jsonify({"error": "Meal already exists"}), 400

    meal = Meal(
        name=data["name"],
        ingredients=data.get("ingredients", [])
    )

    db.session.add(meal)
    db.session.commit()

    return jsonify({"success": True})

@app.route("/meal/<int:id>", methods=["PUT"])
def update_meal(id):
    meal = db.session.get(Meal, id)

    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    data = request.json

    meal.name = data.get("name", meal.name)
    meal.ingredients = data.get("ingredients", meal.ingredients)

    db.session.commit()

    return jsonify({"success": True})

    

@app.route("/meal/<int:id>", methods=["DELETE"])
def delete_meal(id):
    meal = db.session.get(Meal, id)

    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    db.session.delete(meal)
    db.session.commit()

    return jsonify({"success": True})

@app.route("/meals", methods=["GET"])
def get_meals():
    meals = Meal.query.all()
    return jsonify([m.to_dict() for m in meals])

@app.route("/menu/week", methods=["GET"])
def generate_week():
    global current_week 
    meals = Meal.query.all()
    
    if len(meals) < 7:
        return jsonify({"error": "Add at least 7 meals"}), 400

    # ✅ Get last menu
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()

    used_meal_names = set()

    if last_menu:
        for day, meal in last_menu.meals.items():
            used_meal_names.add(meal["name"])

    # ✅ Filter out previously used meals
    available_meals = [m for m in meals if m.name not in used_meal_names]

    # ⚠️ If not enough fresh meals, fallback to all
    if len(available_meals) < 7:
        available_meals = meals

    selected = random.sample(available_meals, 7)

    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    result = {
        days[i]: selected[i].to_dict()
        for i in range(7)
    }

    # ✅ Save new menu
    menu = WeeklyMenu(meals=result)
    db.session.add(menu)
    db.session.commit()

    return jsonify(result)

@app.route("/grocery", methods=["GET"])
def grocery():
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()

    if not last_menu:
        return jsonify({"error": "Generate a menu first"}), 400

    grocery = {}

    # 🔹 Count ingredients
    for day, meal in last_menu.meals.items():
        for item in meal["ingredients"]:
            grocery[item] = grocery.get(item, 0) + 1

    # 🔹 Group ingredients
    grouped = {}

    for item, qty in grocery.items():
        category = categorize_ingredient(item)

        if category not in grouped:
            grouped[category] = []

        grouped[category].append({
            "item": item,
            "qty": qty
        })

    # 🔥 AI enhancement (AFTER grouping is complete)
    try:
        ai_result = enhance_grocery_list(grouped)
        return ai_result  # optional: may return string
    except Exception as e:
        print("AI ERROR:", e)
        return jsonify(grouped)  # fallback
    

if __name__ == "__main__":
    app.run(debug=True)