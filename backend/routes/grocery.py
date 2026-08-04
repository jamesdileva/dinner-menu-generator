"""Grocery-list route (audit §4.1).

Blueprint: `grocery_bp`
  GET /grocery  categorised grocery list from the last weekly menu
"""

from flask import Blueprint, jsonify

from services.grocery_service import build_grocery_list

grocery_bp = Blueprint("grocery_bp", __name__)


@grocery_bp.route("/grocery", methods=["GET"])
def grocery():
    try:
        result = build_grocery_list()
        if isinstance(result, tuple):
            error, status = result
            return jsonify(error), status
        return jsonify(result)
    except Exception as e:
        print("❌ ERROR /grocery:", e)
        return jsonify({"error": str(e)}), 500
