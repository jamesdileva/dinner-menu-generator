"""Data import/export + maintenance routes (audit §4.1).

Blueprint: `data_bp`
  GET  /export        dump all meals + menus as JSON
  POST /import        import meals + menus from a JSON body
  GET,POST /import-file  import from ?path=<file>, a multipart `file` upload,
                          or the legacy `backup.json` fallback (audit §5.4)
  GET  /fix-data      cleanse/normalise meals in place (§5.6 — unprotected, deferred)
  GET  /init-db       create tables (§5.5 — unprotected, deferred)

NOTE: §5.5/§5.6/§8.1 (protecting `fix-data`/`init-db`/`import-file`) are explicitly
deferred per audit.md; these endpoints keep their current unprotected behaviour so the
refactor stays behaviour-preserving. `/import-file` is local-desktop only: a `?path=`
parameter lets the trusted local user point at any existing JSON file.
"""

import json
import os

from flask import Blueprint, jsonify, request

from models import Meal, WeeklyMenu, db
from utils import generate_ingredients, normalize_ingredients, clean_meal_name

data_bp = Blueprint("data_bp", __name__)


def _split_payload(data):
    """Accept either a bare meals list or a {"meals":..., "menus":...} dict."""
    if isinstance(data, list):
        return data, []
    if isinstance(data, dict):
        return data.get("meals", []), data.get("menus", [])
    return [], []


def _ingest(data):
    """Persist an import payload. Shared by /import and /import-file (audit §5.4).

    Idempotent: meals that already exist (case-insensitive name match) are skipped;
    entries without a name are skipped rather than raising KeyError.
    Returns (meals_added, menus_added).
    """
    meals, menus = _split_payload(data)
    added = 0

    for m in meals:
        name = m.get("name", "").strip() if isinstance(m, dict) else ""
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

    for menu in menus:
        db.session.add(WeeklyMenu(meals=menu))

    db.session.commit()
    return added, len(menus)


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
    added, _menus = _ingest(data)
    return {"status": "imported", "added": added}


@data_bp.route("/import-file", methods=["GET", "POST"])
def import_file():
    """Import from a file: `?path=<json file>`, a multipart `file` upload, or the
    legacy `backend/backup.json`. (audit §5.4)"""
    # mode 1: multipart file upload
    upload = request.files.get("file")
    if upload and upload.filename:
        raw = upload.read()
        source_desc = f"upload {upload.filename}"
    else:
        # mode 2: explicit path param, or mode 3: legacy fallback
        path = request.args.get("path")
        if path:
            file_path = os.path.abspath(os.path.expanduser(path))
        else:
            file_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "backup.json")
            )

        print("📂 IMPORT PATH:", file_path)
        print("📂 EXISTS:", os.path.exists(file_path))

        if not os.path.isfile(file_path):
            return jsonify({"error": f"File not found: {file_path}"}), 404

        try:
            with open(file_path, "rb") as f:
                raw = f.read()
        except OSError as e:
            return jsonify({"error": f"Could not read file: {e}"}), 500
        source_desc = file_path

    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return jsonify({"error": f"Invalid JSON in {source_desc}: {e}"}), 400

    added, menus = _ingest(data)
    print(f"✅ Imported from {source_desc}: {added} meals + {menus} menus")
    return jsonify({
        "status": "imported",
        "source": source_desc,
        "meals": added,
        "menus": menus
    })


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
