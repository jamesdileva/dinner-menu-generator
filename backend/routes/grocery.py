"""Grocery-list route (audit §4.1).

Blueprint: `grocery_bp`
  GET    /grocery               categorised grocery list from the last weekly menu
  GET    /grocery/export        downloadable grocery list (audit §5.16): CSV (default) or text
  GET    /grocery/extras        user-added grocery extras on the last menu (audit B3a)
  PUT    /grocery/extras        replace extras on the last menu (audit B3a)
  GET    /grocery/purchased     checked-off items on the last menu (§13.3)
  PUT    /grocery/purchased     replace the checked-off items list (§13.3)
  POST   /grocery/purchased/<item>  toggle a single item's checked-off state (§13.3)
  GET    /savings               list all saved groceries (§13.3b catalog, snacks + staples)
  POST   /saving                add an item to the catalog (auto-groups as snack/staple)

"""

import csv
import io
import logging

from flask import Blueprint, jsonify, request, Response

from models import SavedGrocery, db
from utils import sanitize_text, categorize_ingredient
from services.grocery_service import (
    build_grocery_list,
    enhance_grocery_list,
    get_extras,
    set_extras,
    get_purchased,
    set_purchased,
    toggle_purchased,
)

grocery_bp = Blueprint("grocery_bp", __name__)
logger = logging.getLogger(__name__)


@grocery_bp.route("/grocery", methods=["GET"])
def grocery() -> Response:
    try:
        result = build_grocery_list()
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception:
        logger.exception("ERROR /grocery")
        return jsonify({"error": "Internal server error"}), 500


@grocery_bp.route("/grocery/enhance", methods=["GET"])
def grocery_enhance() -> Response:
    """§16.2 — optionally AI-enhanced grocery list (store-layout order + missing items).

    Falls back to rule-based categorised list when Ollama is disabled or unreachable.
    """
    try:
        result = enhance_grocery_list()
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception:
        logger.exception("ERROR /grocery/enhance")
        return jsonify({"error": "Internal server error"}), 500


@grocery_bp.route("/grocery/extras", methods=["GET"])
def grocery_extras() -> Response:
    try:
        result = get_extras()
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception:
        logger.exception("ERROR /grocery/extras")
        return jsonify({"error": "Internal server error"}), 500


# audit B3a — replace the latest menu's extras (e.g. after removing an item)
@grocery_bp.route("/grocery/extras", methods=["PUT"])
def replace_extras() -> Response:
    data = request.get_json(silent=True) or {}
    try:
        items = data.get("items", []) if isinstance(data, dict) else []
        result = set_extras(items)
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception:
        logger.exception("ERROR PUT /grocery/extras")
        return jsonify({"error": "Internal server error"}), 500


# §13.3 — checked-off grocery items on the last weekly menu
@grocery_bp.route("/grocery/purchased", methods=["GET"])
def grocery_purchased() -> Response:
    try:
        result = get_purchased()
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception:
        logger.exception("ERROR GET /grocery/purchased")
        return jsonify({"error": "Internal server error"}), 500


@grocery_bp.route("/grocery/purchased", methods=["PUT"])
def replace_purchased() -> Response:
    data = request.get_json(silent=True) or {}
    try:
        items = data.get("items", []) if isinstance(data, dict) else []
        result = set_purchased(items)
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception:
        logger.exception("ERROR PUT /grocery/purchased")
        return jsonify({"error": "Internal server error"}), 500


@grocery_bp.route("/grocery/purchased/<item>", methods=["POST"])
def toggle_purchased_route(item: str) -> Response:
    """Toggle a single item's checked-off state (§13.3).

    The `<item>` path segment is URL-decoded by Flask; we normalize it server-side
    (strip + lowercase) before matching against the stored purchased list.
    """
    try:
        result = toggle_purchased(item)
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception:
        logger.exception("ERROR POST /grocery/purchased/<item>")
        return jsonify({"error": "Internal server error"}), 500


# §13.3b — persistent grocery catalog (snacks + staples); renamed from Snack → SavedGrocery
@grocery_bp.route("/savings", methods=["GET"])
def list_savings() -> Response:
    savings = SavedGrocery.query.order_by(SavedGrocery.name.asc()).all()
    return jsonify({"savings": [s.to_dict() for s in savings]})


@grocery_bp.route("/saving", methods=["POST"])
def add_saving() -> Response:
    data = request.get_json(silent=True) or {}
    name = sanitize_text(data.get("name", ""), max_len=100)
    if not name:
        return jsonify({"error": "Item name is required"}), 400

    normalized = name.lower()
    existing = SavedGrocery.query.filter(db.func.lower(SavedGrocery.name) == normalized).first()
    if existing:
        # idempotent: already saved — return it rather than 409 so the frontend
        # doesn't flinch when re-saving the same item.
        return jsonify({"success": True, "saving": existing.to_dict(), "created": False}), 200

    # §13.3b — auto-categorize into snacks vs. staples using the same aisle logic
    # the grocery builder uses (categorize_ingredient expects lowercase input).
    # An explicit `group` override ("snacks" or "staples") is accepted so the
    # frontend's "+ Add Snack" / "+ Add Staple" badges can force the bucket.
    forced_group = sanitize_text(data.get("group", ""), max_len=20)
    if forced_group in ("snacks", "staples"):
        group = forced_group
    else:
        category = categorize_ingredient(name.lower())
        group = "snacks" if category == "Snacks" else "staples"

    saving = SavedGrocery(name=name, group=group)
    db.session.add(saving)
    db.session.commit()
    return jsonify({"success": True, "saving": saving.to_dict(), "created": True}), 201


@grocery_bp.route("/saving/<int:id>", methods=["DELETE"])
def delete_saving(id: int) -> Response:
    saving = db.session.get(SavedGrocery, id)
    if not saving:
        return jsonify({"error": "Item not found"}), 404
    db.session.delete(saving)
    db.session.commit()
    return jsonify({"success": True})


# §13.3b — backward-compatible aliases (old /snacks, /snack, /snack/<id> endpoints)
@grocery_bp.route("/snacks", methods=["GET"])
def list_snacks_alias() -> Response:
    """@deprecated use /savings. Kept for backward-compat with existing frontend deployments."""
    return list_savings()


@grocery_bp.route("/snack", methods=["POST"])
def add_snack_alias() -> Response:
    """@deprecated use /saving. Kept for backward-compat."""
    return add_saving()


@grocery_bp.route("/snack/<int:id>", methods=["DELETE"])
def delete_snack_alias(id: int) -> Response:
    """@deprecated use /saving/<id>. Kept for backward-compat."""
    return delete_saving(id)


@grocery_bp.route("/grocery/export", methods=["GET"])
def export_grocery() -> Response:
    fmt = request.args.get("format", "csv").lower()
    try:
        result = build_grocery_list()
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
    except Exception:
        logger.exception("ERROR /grocery/export")
        return jsonify({"error": "Internal server error"}), 500

    if fmt == "text":
        buf = io.StringIO()
        for category, items in result.items():
            buf.write(f"{category}\n")
            for i in items:
                # §13.3 — annotate checked items
                prefix = "[x] " if i.get("purchased") else "[ ] "
                buf.write(f"  - {prefix}{i['item']} ({i['qty']})\n")
            buf.write("\n")
        data, filename, mimetype = buf.getvalue(), "grocery_list.txt", "text/plain"
    else:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Category", "Item", "Quantity", "Purchased"])
        for category, items in result.items():
            for i in items:
                # §13.3 — mark purchased column as Yes/No
                purchased = "Yes" if i.get("purchased") else "No"
                writer.writerow([category, i["item"], i["qty"], purchased])
        data, filename, mimetype = buf.getvalue(), "grocery_list.csv", "text/csv"

    return Response(
        data,
        mimetype=mimetype,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
