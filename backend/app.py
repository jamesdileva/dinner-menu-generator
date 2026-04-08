from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import random
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

# ✅ ROUTES
@app.route("/")
def home():
    return "API running"
    
@app.route("/init-db")
def init_db():
    db.create_all()
    return "DB initialized"

@app.route("/meal", methods=["POST"])
def add_meal():
    data = request.json

    meal = Meal(
        name=data["name"],
        ingredients=data.get("ingredients", [])
    )

    db.session.add(meal)
    db.session.commit()

    return jsonify({"success": True})

@app.route("/meal/<int:id>", methods=["PUT"])
def update_meal(id):
    meal = Meal.query.get(id)

    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    data = request.json

    meal.name = data.get("name", meal.name)
    meal.ingredients = data.get("ingredients", meal.ingredients)

    db.session.commit()

    return jsonify({"success": True})

@app.route("/meal/<int:id>", methods=["DELETE"])
def delete_meal(id):
    meal = Meal.query.get(id)

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

    for day, meal in last_menu.meals.items():
        for item in meal["ingredients"]:
            grocery[item] = grocery.get(item, 0) + 1

    return jsonify(grocery)
    

if __name__ == "__main__":
    app.run(debug=True)