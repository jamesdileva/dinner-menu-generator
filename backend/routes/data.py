"""Data import/export routes (audit §4.1 / §5.4).

Blueprint: `data_bp`
  GET  /export        dump all meals + menus as JSON
  POST /import        import meals + menus from a JSON body
  GET,POST /import-file  import from `?path=<file>`, a multipart upload, or legacy
                          `backup.json` (§5.4)

NOTE: `/fix-data` and `/init-db` were previously exposed here as HTTP routes
(audit §5.5/§5.6/§8.1). They are now **Flask CLI commands** only (see `backend/cli.py`),
removing them from the production HTTP surface. `/import-file` is intentionally kept as
an HTTP endpoint: per §5.4 it is the user-facing data-import feature (additive + deduping,
non-destructive).
"""

import json
import os
import logging

from typing import Any, Dict, List, Tuple

from flask import Blueprint, jsonify, request
from flask.wrappers import Response

from models import Meal, WeeklyMenu, db
from services.menu_service import expand_menu
from utils import sanitize_text, sanitize_ingredients, normalize_ingredients

data_bp = Blueprint("data_bp", __name__)
logger = logging.getLogger(__name__)


def _split_payload(data: Any) -> Tuple[List[Dict[str, Any]], List[Any]]:
    """Accept either a bare meals list or a {"meals":..., "menus":...} dict."""
    if isinstance(data, list):
        return data, []
    if isinstance(data, dict):
        return data.get("meals", []), data.get("menus", [])
    return [], []


def _ingest(data: Any) -> Tuple[int, int]:
    """Persist an import payload. Shared by /import and /import-file (audit §5.4).

    Idempotent: meals that already exist (case-insensitive name match) are skipped;
    entries without a name are skipped rather than raising KeyError.
    Returns (meals_added, menus_added).
    """
    meals, menus = _split_payload(data)
    added = 0

    for m in meals:
        if not isinstance(m, dict):
            continue
        # §8.6 sanitize name + ingredients before persisting
        name = sanitize_text(m.get("name", ""), max_len=100)
        if not name:
            continue

        existing = Meal.query.filter(db.func.lower(Meal.name) == name.lower()).first()
        if existing:
            continue

        ingredients = normalize_ingredients(sanitize_ingredients(m.get("ingredients", [])))
        category = sanitize_text(m.get("category", ""), max_len=50)  # §5.14

        db.session.add(Meal(name=name, ingredients=ingredients, category=category or None))
        added += 1

    for menu in menus:
        # §5.4 — backup.json exports menus as {"id": <int>, "meals": {day: ...}}.
        # Extract the inner `meals` key so we don't nest the whole dict as the column value
        # (which creates unreadable "empty" menus in the UI). If the entry is already a bare
        # dict of day mappings (legacy format), store it as-is.
        if isinstance(menu, dict) and "meals" in menu and "id" in menu:
            stored = menu["meals"]
        elif isinstance(menu, dict):
            stored = menu
        else:
            continue
        db.session.add(WeeklyMenu(meals=stored))

    db.session.commit()
    return added, len(menus)


@data_bp.route("/export")
def export_data() -> Response:
    meals = Meal.query.all()
    weekly = WeeklyMenu.query.all()
    return jsonify(
        {
            "meals": [m.to_dict() for m in meals],
            "menus": [expand_menu(m.meals) for m in weekly],  # §5.13 expand ids -> full meals
        }
    )


@data_bp.route("/import", methods=["POST"])
def import_data() -> Response:
    data = request.json or {}
    added, _menus = _ingest(data)
    return {"status": "imported", "added": added}


@data_bp.route("/import-file", methods=["GET", "POST"])
def import_file() -> Response:
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

        logger.info("Import path: %s (exists=%s)", file_path, os.path.exists(file_path))

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
    logger.info("Imported from %s: %d meals + %d menus", source_desc, added, menus)
    return jsonify({"status": "imported", "source": source_desc, "meals": added, "menus": menus})


# /fix-data and /init-db are now Flask CLI commands (see ../cli.py, audit §5.5/§5.6/8.1).
