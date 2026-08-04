"""Data import/export + maintenance routes (audit §4.1).

Blueprint: `data_bp`
  GET  /export        dump all meals + menus as JSON
  POST /import        import meals + menus from a JSON body
  GET  /import-file   import from the bundled `backup.json` (§5.4 — hardcoded path, preserved)
  GET  /fix-data      cleanse/normalise meals in place (§5.6 — unprotected, preserved)
  GET  /init-db       create tables (§5.5 — unprotected, preserved)

NOTE: §5.5/§5.6/§8.1 (protecting `fix-data`/`init-db`/`import-file`) are explicitly
deferred per audit.md; these endpoints keep their current unprotected behaviour so the
refactor stays behaviour-preserving.
"""

import json
import os

from flask import Blueprint, jsonify, request

from models import Meal, WeeklyMenu, db
from utils import generate_ingredients, normalize_ingredients, clean_meal_name

data_bp = Blueprint("data_bp", __name__)


@data_bp.route("/export")
def export_data():
    meals = Meal.query.all()
    weekly = WeeklyMenu.query.all()
    return jsonify({
        "meals": [m.to_dict() for m in meals],
        "menus": [m.meals for m in weekly]
    })


@data_bp.route("/import", methods=["POST"])
def import_data():
    data = request.json or {}
    added = 0

    for m in data.get("meals", []):
        name = m.get("name", "").strip()
        if not name:
            continue

        existing = Meal.query.filter(
            db.func.lower(Meal.name) == name.lower()
        ).first()
        if existing:
            continue

        db.session.add(Meal(
            name=name,
            ingredients=m.get("ingredients", [])
        ))
        added += 1

    for menu in data.get("menus", []):
        db.session.add(WeeklyMenu(meals=menu))

    db.session.commit()
    return {"status": "imported", "added": added}


@data_bp.route("/import-file")
def import_file():
    path = os.path.join(os.path.dirname(__file__), "..", "backup.json")
    path = os.path.abspath(path)

    print("📂 IMPORT PATH:", path)
    print("📂 EXISTS:", os.path.exists(path))

    if not os.path.exists(path):
        return f"❌ backup.json not found at {path}"

    with open(path) as f:
        data = json.load(f)

    # support both formats
    if isinstance(data, list):
        meals = data
        menus = []
    else:
        meals = data.get("meals", [])
        menus = data.get("menus", [])

    for m in meals:
        existing = Meal.query.filter_by(name=m["name"]).first()
        if not existing:
            db.session.add(Meal(
                name=m["name"],
                ingredients=m.get("ingredients", [])
            ))

    for menu in menus:
        db.session.add(WeeklyMenu(meals=menu))

    db.session.commit()
    return f"✅ Imported {len(meals)} meals + {len(menus)} menus"


@data_bp.route("/fix-data")
def fix_data():
    meals = Meal.query.all()
    seen_names = set()

    for meal in meals:
        combined = " ".join(meal.ingredients) if meal.ingredients else ""

        # backfill if empty
        if not combined.strip():
            meal.ingredients = generate_ingredients(meal.name)
        else:
            meal.ingredients = normalize_ingredients(combined)

        cleaned_name = clean_meal_name(meal.name)
        normalized = cleaned_name.lower()

        # remove duplicates
        if normalized in seen_names:
            db.session.delete(meal)
            continue

        seen_names.add(normalized)
        meal.name = cleaned_name

    db.session.commit()
    return "Data fully cleaned!"


@data_bp.route("/init-db")
def init_db():
    db.create_all()
    return "DB initialized"
