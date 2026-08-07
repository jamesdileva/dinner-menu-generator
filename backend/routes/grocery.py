"""Grocery-list route (audit §4.1).

Blueprint: `grocery_bp`
  GET  /grocery          categorised grocery list from the last weekly menu
  GET  /grocery/export   downloadable grocery list (audit §5.16): CSV (default) or text
  GET  /grocery/extras   user-added grocery extras on the last menu (audit B3a)
  PUT  /grocery/extras   replace extras on the last menu (audit B3a)
"""

import csv
import io
import logging
from flask import Blueprint, jsonify, request, Response

from services.grocery_service import build_grocery_list, get_extras, set_extras

grocery_bp = Blueprint("grocery_bp", __name__)
logger = logging.getLogger(__name__)


@grocery_bp.route("/grocery", methods=["GET"])
def grocery():
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
def grocery_extras():
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
def replace_extras():
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


@grocery_bp.route("/grocery/export", methods=["GET"])
def export_grocery():
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
                buf.write(f"  - {i['item']} ({i['qty']})\n")
            buf.write("\n")
        data, filename, mimetype = buf.getvalue(), "grocery_list.txt", "text/plain"
    else:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Category", "Item", "Quantity"])
        for category, items in result.items():
            for i in items:
                writer.writerow([category, i["item"], i["qty"]])
        data, filename, mimetype = buf.getvalue(), "grocery_list.csv", "text/csv"

    return Response(
        data,
        mimetype=mimetype,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
