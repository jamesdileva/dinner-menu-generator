"""Meal CRUD + OCR menu import routes (audit §4.1).

Blueprint: `meals_bp`
  GET  /meals            list meals (paginated)        (audit §4.7)
  POST /meal             create a meal
  PUT  /meal/<int:id>    update a meal
  DEL  /meal/<int:id>    delete a meal
  POST /upload-menu      OCR an uploaded image -> meals (audit §4.5/§4.6)
"""

import io
import logging

import cv2
import numpy as np
from PIL import Image
import pytesseract
from flask import Blueprint, jsonify, request

from models import Meal, db
from utils import (
    is_valid_meal,
    clean_meal_name,
    generate_ingredients,
    normalize_ingredients,
    sanitize_text,
    sanitize_ingredients,
    tesseract_path,
)
from limiter import limiter  # audit §5.21 — per-route rate limit (OCR is heavier)

meals_bp = Blueprint("meals_bp", __name__)
logger = logging.getLogger(__name__)


@meals_bp.route("/meals", methods=["GET"])
def get_meals():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    limit = min(max(limit, 1), 100)

    query = Meal.query
    category = request.args.get("category")
    if category:  # §5.14 filter meals by category (case-insensitive)
        cat = sanitize_text(category, max_len=50)
        if cat:
            query = query.filter(Meal.category.ilike(f"%{cat}%"))

    search = request.args.get("search")
    if search:  # §5.18 search by name (case-insensitive substring)
        s = sanitize_text(search, max_len=100)
        if s:
            query = query.filter(Meal.name.ilike(f"%{s}%"))

    pagination = query.order_by(Meal.name.asc()).paginate(page=page, per_page=limit)

    return jsonify(
        {
            "meals": [m.to_dict() for m in pagination.items],
            "page": page,
            "limit": limit,
            "total": pagination.total,
            "pages": pagination.pages,
            "search": search or "",
        }
    )


@meals_bp.route("/meals/categories", methods=["GET"])
def get_meal_categories():
    """Distinct, non-empty meal categories (for the frontend filter dropdown). §5.14"""
    rows = db.session.query(Meal.category).filter(Meal.category.isnot(None)).distinct().all()
    categories = sorted([r[0] for r in rows if r[0]])
    return jsonify({"categories": categories})


@meals_bp.route("/meal", methods=["POST"])
def add_meal():
    data = request.json or {}

    raw_name = data.get("name", "")
    if not raw_name or not raw_name.strip():
        return jsonify({"error": "Meal name is required"}), 400

    # §8.6 sanitize storage name: strip control chars, collapse whitespace, cap length
    name = sanitize_text(raw_name.strip(), max_len=100)
    if not name:
        return jsonify({"error": "Meal name is required"}), 400

    normalized = name.lower()

    existing = Meal.query.filter(db.func.lower(Meal.name) == normalized).first()

    if existing:
        return jsonify({"error": "Meal already exists"}), 400

    ingredients = normalize_ingredients(sanitize_ingredients(data.get("ingredients", [])))
    category = sanitize_text(data.get("category", ""), max_len=50)  # §5.14

    meal = Meal(name=name, ingredients=ingredients, category=category or None)
    db.session.add(meal)
    db.session.commit()

    return jsonify({"success": True})


@meals_bp.route("/meal/<int:id>", methods=["PUT"])
def update_meal(id):
    meal = db.session.get(Meal, id)
    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    data = request.get_json(silent=True) or {}
    # §8.6 sanitize + normalise stored fields (control char / whitespace / length bounds)
    if "name" in data:
        meal.name = sanitize_text(data.get("name"), max_len=100)
    if "ingredients" in data:
        meal.ingredients = normalize_ingredients(sanitize_ingredients(data.get("ingredients", [])))
    if "category" in data:  # §5.14
        meal.category = sanitize_text(data.get("category"), max_len=50) or None
    db.session.commit()

    return jsonify({"success": True})


@meals_bp.route("/meal/<int:id>", methods=["DELETE"])
def delete_meal(id):
    meal = db.session.get(Meal, id)
    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    db.session.delete(meal)
    db.session.commit()

    return jsonify({"success": True})


@meals_bp.route("/upload-menu", methods=["POST"])
@limiter.limit("5/minute")  # audit §8.4 — protect the OCR/Tesseract endpoint
def upload_menu():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files["image"]
        if not file or file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # §4.6 validate content type
        allowed_types = {"image/png", "image/jpeg", "image/jpg"}
        mimetype = file.mimetype or ""
        if mimetype not in allowed_types:
            return jsonify({"error": f"Unsupported file type: {mimetype or 'unknown'}"}), 400

        # §4.6 enforce file size (5 MB)
        file.seek(0, io.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > 5 * 1024 * 1024:
            return jsonify({"error": "File too large (max 5 MB)"}), 400

        # §4.6 read + validate image (corrupt / invalid files)
        try:
            image = Image.open(file).convert("RGB")
        except Exception:
            return jsonify({"error": "Could not read image (corrupt or invalid)"}), 400

        # §4.6 dimension guard (4000px)
        if image.width > 4000 or image.height > 4000:
            return jsonify({"error": "Image too large (max 4000x4000)"}), 400

        # convert to OpenCV format
        img = np.array(image)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)

        config = "--psm 4"

        # §4.5 friendly error if the OCR engine is unavailable
        if not tesseract_path:
            return (
                jsonify(
                    {"error": "OCR not available: install Tesseract OCR and add it to your PATH"}
                ),
                503,
            )

        text = pytesseract.image_to_string(thresh, config=config)
        logger.debug("RAW OCR:\n%s", text)

        # split into lines FIRST, then filter
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        lines = [_l for _l in lines if is_valid_meal(_l)]

        cleaned_meals = []
        for line in lines:
            if len(line) < 3:
                continue
            cleaned = clean_meal_name(line)
            if not cleaned:
                continue
            cleaned_meals.append(cleaned)

        added = []
        skipped = []
        updated = []
        for meal_name in cleaned_meals:
            name_lower = meal_name.lower()

            existing = Meal.query.filter(db.func.lower(Meal.name) == name_lower).first()

            if existing:
                # NEW LOGIC: fill missing ingredients
                if not existing.ingredients or len(existing.ingredients) == 0:
                    existing.ingredients = generate_ingredients(meal_name)
                    updated.append(meal_name)
                else:
                    skipped.append(meal_name)
                continue

            meal = Meal(name=meal_name, ingredients=generate_ingredients(meal_name))
            db.session.add(meal)
            added.append(meal_name)

        db.session.commit()

        return jsonify({"added": added, "updated": updated, "skipped": skipped})

    except Exception:
        logger.exception("ERROR /upload-menu")
        return jsonify({"error": "Internal server error"}), 500
