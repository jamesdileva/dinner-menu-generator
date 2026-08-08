"""Menu generation + daily-pick routes (audit §4.1).

Blueprint: `menu_bp`
  GET  /menu/today        quick pick: random home meal (no repeats today)
  GET  /menu/takeout      quick pick: random takeout spot
  GET  /menu/decide       quick pick: home OR takeout
  GET  /menu/week         generate a 7-day weekly menu
  POST /menu/reroll/<day> reroll one day of the last weekly menu
  GET  /menus             list all saved weekly menus (history view, §5.15)
  GET  /insights          macro overview + deficiency flags + swap tips (audit B2)
"""

import logging
from typing import Any, Dict, Tuple, Union

from flask import Blueprint, jsonify, request
from flask.wrappers import Response

from services.menu_service import (
    pick_today,
    pick_takeout,
    decide,
    generate_week,
    reroll_day,
    set_menu_day,
    expand_menu,
    list_menus,
)
from services.nutrition_service import insights

menu_bp = Blueprint("menu_bp", __name__)
logger = logging.getLogger(__name__)


def _respond(result: Union[Dict[str, Any], Tuple[Dict[str, Any], int]]) -> Response:
    """A service helper returns either a dict (success) or an (error, status) tuple."""
    if isinstance(result, tuple):
        error, status = result
        return jsonify(error), status
    return jsonify(result)


@menu_bp.route("/menu/today", methods=["GET"])
def meal_today() -> Response:
    return _respond(pick_today())


@menu_bp.route("/menu/takeout", methods=["GET"])
def takeout() -> Response:
    return jsonify(pick_takeout())


@menu_bp.route("/menu/decide", methods=["GET"])
def decide_route() -> Response:
    return _respond(decide())


@menu_bp.route("/menu/week", methods=["GET"])
def week() -> Response:
    try:
        result = generate_week()
        # §5.13 menus store meal ids; expand to full dicts for the frontend display
        if isinstance(result, dict):
            result = expand_menu(result)
        return _respond(result)
    except Exception:
        logger.exception("ERROR /menu/week")
        return jsonify({"error": "Internal server error"}), 500


@menu_bp.route("/menu/reroll/<day>", methods=["POST"])
def reroll(day: str) -> Response:
    return _respond(reroll_day(day))


@menu_bp.route("/menu/<day>", methods=["PUT"])
def set_day(day: str) -> Response:
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict) or "name" not in data:
        return jsonify({"error": "Invalid meal payload (need {name, ingredients})"}), 400
    return _respond(set_menu_day(day, data))


@menu_bp.route("/menus", methods=["GET"])
def menus() -> Response:
    """Menu history: list all saved weekly menus, newest first (audit §5.15)."""
    return _respond(list_menus())


@menu_bp.route("/insights", methods=["GET"])
def insights_route() -> Response:
    """Audit B2: last-few-weeks macro overview + deficiency flags + swap suggestions."""
    return _respond(insights())
