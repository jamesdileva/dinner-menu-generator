"""Menu generation + daily-pick routes (audit §4.1).

Blueprint: `menu_bp`
  GET  /menu/today        quick pick: random home meal (no repeats today)
  GET  /menu/takeout      quick pick: random takeout spot
  GET  /menu/decide       quick pick: home OR takeout
  GET  /menu/week         generate a 7-day weekly menu
  POST /menu/reroll/<day> reroll one day of the last weekly menu
"""

from flask import Blueprint, jsonify

from services.menu_service import (
    pick_today,
    pick_takeout,
    decide,
    generate_week,
    reroll_day,
)

menu_bp = Blueprint("menu_bp", __name__)


def _respond(result):
    """A service helper returns either a dict (success) or an (error, status) tuple."""
    if isinstance(result, tuple):
        error, status = result
        return jsonify(error), status
    return jsonify(result)


@menu_bp.route("/menu/today", methods=["GET"])
def meal_today():
    return _respond(pick_today())


@menu_bp.route("/menu/takeout", methods=["GET"])
def takeout():
    return jsonify(pick_takeout())


@menu_bp.route("/menu/decide", methods=["GET"])
def decide_route():
    return _respond(decide())


@menu_bp.route("/menu/week", methods=["GET"])
def week():
    try:
        return _respond(generate_week())
    except Exception as e:
        print("❌ ERROR /menu/week:", e)
        return jsonify({"error": str(e)}), 500


@menu_bp.route("/menu/reroll/<day>", methods=["POST"])
def reroll(day):
    return _respond(reroll_day(day))
