from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
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

def merge_ingredient(name):
    return INGREDIENT_MAP.get(name, name)  

IGNORE_WORDS = [
    "mix",
    "premade",
    "or",
    "white",
    "sub",
    "sandwich"
]
IGNORE_WORDS.append("sauce")
IGNORE_WORDS.extend([
    "and"
])
KEEP_TOGETHER = [
    "pancake mix",
    "tomato sauce",
    "soy sauce",
    "hot sauce",
    "bbq sauce",
    "premade lasagna",
    "lasagna",
    "rice pilaf",
    "angel hair pasta",
    "ground beef",
    "tri tip",
    "pork chop",
    "white rice",
]

INGREDIENT_MAP = {
    "chicken breast": "chicken",
    "chicken thigh": "chicken",
    "ground beef": "beef",
    "steak": "beef",
    "shredded cheese": "cheese",
    "mozzarella cheese": "cheese",
    "white rice": "rice",
    "brown rice": "rice",
    "tri tip": "beef",
    "tri": "beef",
    "tip": "beef",
    "angelhair": "pasta",
    "noodle": "pasta"
}
INGREDIENT_MAP.update({
    "potatoe": "potato",
    "veggie": "vegetable",
    "meat": "beef",
    "roast": "pork",
    "stew": "beef stew",
    "green": "green chili",
    "chili": "green chili",
    "pancake": "pancake mix",
    "angel hair pasta": "pasta"
})
KEEP_TOGETHER.extend([
    "green chili",
    "chicken burritos",
    "pork roast",
    "beef tacos",
    "veggie stir fry",
    "angel hair pasta"
    "pancake mix",
    "beef stew"
])
def clean_meal_name(name):
    if not name:
        return name

    name = name.strip()

    # remove extra spaces
    name = " ".join(name.split())

    # fix casing (Title Case)
    name = name.title()

    # quick typo fixes (you can expand this later)
    fixes = {
        "Lasagnaa": "Lasagna",
        "Taco Boowl": "Taco Bowl",
        "Veggistir- Fry": "Veggie Stir Fry"
    }

    return fixes.get(name, name)

def normalize_ingredients(ingredients):
    result = []

    if isinstance(ingredients, list):
        items = ingredients
    else:
        items = [ingredients]

    for item in items:
        if not item:
            continue

        item = item.lower().strip()

        # 🔥 check protected phrases FIRST
        normalized_item = " ".join(item.lower().split())

        matched = False
        for phrase in KEEP_TOGETHER:
            if phrase in normalized_item:
                result.append(phrase)
                matched = True
                break

        if matched:
            continue

        # normal splitting
        parts = item.split(",")

        for part in parts:
            sub_parts = part.split(" ")

            for p in sub_parts:
                cleaned = p.strip()

                if not cleaned:
                    continue

                if cleaned.startswith("ingredient"):
                    continue

                if len(cleaned) < 2:
                    continue

                # ignore junk words EARLY
                if cleaned in IGNORE_WORDS:
                    continue

                # singular fix
                if cleaned.endswith("s") and len(cleaned) > 3:
                    cleaned = cleaned[:-1]

                # merge AFTER normalization
                cleaned = merge_ingredient(cleaned)

                result.append(cleaned)

    return result

def categorize_ingredient(item):
    item = item.lower()

    if item in [
        "chicken",
        "beef",
        "pork",
        "egg",
        "shrimp",
        "sausage",
        "bacon",
        "meatball",
        "carne",
        "hamburger",
        "steak"
        "ground beef", 
        "beef stew"   
    ]:
        return "Protein"
        
    if item in ["lettuce", "tomato", "onion", "garlic", "pepper","potato","vegetable"]:
        return "Produce"

    if item in ["milk", "cheese", "butter", "cream"]:
        return "Dairy"

    if item in ["rice", "pasta", "bread", "bun", "tortilla", "pilaf"]:
        return "Grains"

    return "Other"

fast_food_spots = [
    {"name": "McDonald's", "type": "Fast Food"},
    {"name": "Chipotle", "type": "Mexican"},
    {"name": "Pizza Hut", "type": "Pizza"},
    {"name": "Subway", "type": "Sandwiches"},
    {"name": "Chick-fil-A", "type": "Chicken"}
]

def normalize_name(name):
    return name.strip().lower()

# ✅ ROUTES
@app.route("/")
def home():
    return "API running"

@app.route("/fix-data")
def fix_data():
    meals = Meal.query.all()

    seen_names = set()

    for meal in meals:
        # ✅ fix ingredients
        meal.ingredients = normalize_ingredients(meal.ingredients)

        # ✅ fix name
        cleaned_name = clean_meal_name(meal.name)

        # ✅ prevent duplicates after cleaning
        normalized = cleaned_name.lower()

        if normalized in seen_names:
            # optional: delete duplicate
            db.session.delete(meal)
            continue

        seen_names.add(normalized)
        meal.name = cleaned_name

    db.session.commit()

    return "Data fully cleaned!"

@app.route("/init-db")
def init_db():
    db.create_all()
    return "DB initialized"
import random

used_today = set()  # simple in-memory (can upgrade later)

import random

used_today = set()  # avoid repeats

@app.route("/menu/takeout", methods=["GET"])
def takeout():
    import random
    return jsonify(random.choice(fast_food_spots))

@app.route("/menu/decide", methods=["GET"])
def decide():
    import random

    choice = random.choice(["home", "takeout"])

    if choice == "home":
        meals = Meal.query.all()
        meal = random.choice(meals)
        return jsonify({"mode": "home", "meal": meal.to_dict()})

    else:
        return jsonify({"mode": "takeout", "meal": random.choice(fast_food_spots)})    

@app.route("/menu/today", methods=["GET"])
def meal_today():
    global used_today

    meals = Meal.query.all()

    if not meals:
        return jsonify({"error": "No meals available"}), 400

    # filter unused meals
    available = [m for m in meals if m.name not in used_today]

    # reset if we've used all meals
    if not available:
        used_today.clear()
        available = meals

    meal = random.choice(available)

    used_today.add(meal.name)

    return jsonify(meal.to_dict())

@app.route("/menu/reroll/<day>", methods=["POST"])
def reroll_day(day):
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()

    if not last_menu:
        return jsonify({"error": "Generate a menu first"}), 400

    meals = Meal.query.all()

    if len(meals) < 1:
        return jsonify({"error": "No meals available"}), 400

    # avoid current meal for that day
    current_meal_name = last_menu.meals[day]["name"]

    available = [m for m in meals if m.name != current_meal_name]

    import random
    new_meal = random.choice(available)

    last_menu.meals[day] = new_meal.to_dict()
    db.session.commit()

    return jsonify({
        "day": day,
        "meal": new_meal.to_dict()
    })    

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

            cleaned = clean_meal_name(meal_name)

            if not cleaned:
                continue

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

    # ✅ define FIRST
    raw_name = data["name"]
    name = raw_name.strip()
    normalized = raw_name.strip().lower()

    # ✅ check duplicate
    existing = Meal.query.filter(
        db.func.lower(Meal.name) == normalized
    ).first()

    if existing:
        return jsonify({"error": "Meal already exists"}), 400

    # ✅ normalize ingredients
    ingredients = normalize_ingredients(data.get("ingredients", []))

    # ✅ create meal
    meal = Meal(
        name=name,
        ingredients=ingredients
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
    meals = Meal.query.order_by(Meal.name.asc()).all()
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

    for day, meal in last_menu.meals.items():
        for item in meal["ingredients"]:
            grocery[item] = grocery.get(item, 0) + 1

    grouped = {}

    for item, qty in grocery.items():
        category = categorize_ingredient(item)

        if category not in grouped:
            grouped[category] = []

        grouped[category].append({
            "item": item,
            "qty": qty
        })

    return jsonify(grouped)

    # 🔥 AI enhancement (AFTER grouping is complete)
    try:
        ai_result = enhance_grocery_list(grouped)
        return ai_result  # optional: may return string
    except Exception as e:
        print("AI ERROR:", e)
        return jsonify(grouped)  # fallback
    

if __name__ == "__main__":
    app.run(debug=True)