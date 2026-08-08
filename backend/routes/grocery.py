"""Grocery-list route (audit §4.1).

Blueprint: `grocery_bp`
  GET    /grocery               categorised grocery list from the last weekly menu
  GET    /grocery/export        downloadable grocery list (audit §5.16): CSV (default) or text
  GET    /grocery/extras        user-added grocery extras on the last menu (audit B3a)
  PUT    /grocery/extras        replace extras on the last menu (audit B3a)
  GET    /grocery/purchased     checked-off items on the last menu (§13.3)
  PUT    /grocery/purchased     replace the checked-off items list (§13.3)
  POST   /grocery/purchased/<item>  toggle a single item's checked-off state (§13.3)
  GET    /snacks                list all saved snacks (§13.3b catalog)
  POST   /snack                 add a snack to the catalog
  DEL    /snack/<int:id>        delete a snack from the catalog
"""

import csv
import io
import logging

from flask import Blueprint, jsonify, request, Response

from models import Snack, db
from utils import sanitize_text
from services.grocery_service import (
    build_grocery_list,
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


# §13.3b — saved snack catalog (promotable from week extras)
@grocery_bp.route("/snacks", methods=["GET"])
def list_snacks() -> Response:
    snacks = Snack.query.order_by(Snack.name.asc()).all()
    return jsonify({"snacks": [s.to_dict() for s in snacks]})


@grocery_bp.route("/snack", methods=["POST"])
def add_snack() -> Response:
    data = request.get_json(silent=True) or {}
    name = sanitize_text(data.get("name", ""), max_len=100)
    if not name:
        return jsonify({"error": "Snack name is required"}), 400

    normalized = name.lower()
    existing = Snack.query.filter(db.func.lower(Snack.name) == normalized).first()
    if existing:
        # idempotent: already saved — return it rather than 409 so the frontend
        # doesn't flinch when re-saving the same snack.
        return jsonify({"success": True, "snack": existing.to_dict(), "created": False}), 200

    snack = Snack(name=name)
    db.session.add(snack)
    db.session.commit()
    return jsonify({"success": True, "snack": snack.to_dict(), "created": True}), 201


@grocery_bp.route("/snack/<int:id>", methods=["DELETE"])
def delete_snack(id: int) -> Response:
    snack = db.session.get(Snack, id)
    if not snack:
        return jsonify({"error": "Snack not found"}), 404
    db.session.delete(snack)
    db.session.commit()
    return jsonify({"success": True})


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
