"""Business logic for grocery-list generation (audit §4.1).

Ports the aggregation/quantity-parsing/categorisation that lived inline in the
`GET /grocery` route. Pure DB reads here; the route just calls `build_grocery_list()`.
"""

import json
import re
from typing import Any, Dict, List, Tuple, Union

from flask import current_app
from models import Meal, WeeklyMenu, db
from services.llm_service import call_ollama, parse_json_list
from utils import (
    INGREDIENT_MAP,
    parse_quantity,
    categorize_ingredient,
    pluralize_word,
    sanitize_text,
)


# common units to intercept while parsing ingredient strings
UNIT_PATTERN = re.compile(r"\b(lb|lbs|oz|ozs|tsp|tbsp|cup|cups|pack|g|kg|piece|pieces)\b")


def build_grocery_list() -> Union[Dict[str, List[Dict[str, Any]]], Tuple[Dict[str, str], int]]:
    """Build a categorised grocery list from the most-recent weekly menu.

    Returns `({"Protein": [{"item": ..., "qty": ..., "purchased": bool}], ...})` or an
    error tuple `(error_dict, status_code)`.
    """
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400

    # §13.3 — load the purchased set once; items are keyed by normalized name.
    purchased: set = set(last_menu.purchased or [])

    # Structure: { "ingredient_name": { "unit_type": total_quantity } }
    grocery_totals: Dict[str, Dict[str, float]] = {}

    for day, val in last_menu.meals.items():
        # §5.13 storage is meal ids; resolve to the current Meal so the grocery list
        # reflects edited ingredients. Legacy full-snapshot menus are handled too.
        if isinstance(val, int):
            m = db.session.get(Meal, val)
            meal = m.to_dict() if m else {"id": val, "name": None, "ingredients": []}
        elif isinstance(val, dict):
            meal = val
        else:
            continue

        if not meal.get("ingredients"):
            continue

        for raw_item in meal["ingredients"]:
            if not raw_item:
                continue

            # 1. clean & apply ingredient map
            cleaned_str = raw_item.lower().strip()

            # 2. parse quantity + units
            qty = 1.0  # default multiplier
            unit = "count"  # default unit if none found

            num_match = re.match(r"^([0-9\./\s]+)", cleaned_str)
            if num_match:
                num_str = num_match.group(1).strip()
                qty = parse_quantity(num_str)
                # strip numbers from the string
                cleaned_str = cleaned_str[num_match.end() :].strip()

            unit_match = UNIT_PATTERN.search(cleaned_str)
            if unit_match:
                unit = unit_match.group(1)
                # normalize plurals (lbs -> lb)
                if unit.endswith("s") and unit != "sub":
                    unit = unit[:-1]
                cleaned_str = cleaned_str.replace(unit_match.group(0), "", 1).strip()

            # clean up leftover "of" / punctuation ("cans of tomatoes")
            cleaned_str = re.sub(r"^\bof\b", "", cleaned_str).strip()
            cleaned_str = cleaned_str.strip(",.* ")

            normalized_item = INGREDIENT_MAP.get(cleaned_str, cleaned_str)
            if not normalized_item:
                continue

            # 3. aggregate by item AND unit type
            if normalized_item not in grocery_totals:
                grocery_totals[normalized_item] = {}

            grocery_totals[normalized_item][unit] = (
                grocery_totals[normalized_item].get(unit, 0.0) + qty
            )

    # audit B3a — user-added extras attach to this week's menu; treat as count-unit qty-1
    # items that aggregate alongside meal ingredients.
    for raw_item in last_menu.extras or []:
        if not raw_item:
            continue
        cleaned_str = raw_item.lower().strip()
        normalized_item = INGREDIENT_MAP.get(cleaned_str, cleaned_str)
        if not normalized_item:
            continue
        grocery_totals.setdefault(normalized_item, {})
        grocery_totals[normalized_item]["count"] = (
            grocery_totals[normalized_item].get("count", 0.0) + 1.0
        )

    # 4. group by category
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for item, units in grocery_totals.items():
        category = categorize_ingredient(item)
        grouped.setdefault(category, [])

        for unit, total_qty in units.items():
            display_qty = int(total_qty) if total_qty.is_integer() else round(total_qty, 2)

            if unit == "count":
                # §5.11: pluralize the *item name* when more than one
                # (e.g. "tomato" -> "Tomatoes (2)"); mass nouns stay unchanged.
                label = pluralize_word(item) if display_qty != 1 else item
                item_display = label.title()
                qty_str = f"{display_qty}"
            else:
                item_display = item.title()
                qty_str = f"{display_qty} {unit}"
                if display_qty > 1:
                    qty_str += "s"  # pluralize the unit (lb -> lbs, can -> cans, ...)

            # §13.3 — attach purchased flag so the frontend can render checkboxes
            # keyed by the normalized item name (same as the `item` dict key here).
            grouped[category].append(
                {"item": item_display, "qty": qty_str, "purchased": item in purchased}
            )

    return grouped


def get_extras() -> Union[Dict[str, List[str]], Tuple[Dict[str, str], int]]:
    """Return the latest weekly menu's user-added grocery extras (audit B3a)."""
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400
    return {"extras": list(last_menu.extras or [])}


def set_extras(items: List[str]) -> Union[Dict[str, List[str]], Tuple[Dict[str, str], int]]:
    """Replace the latest weekly menu's extras list (audit B3a)."""
    if not isinstance(items, list):
        return {"error": "extras must be a list of strings"}, 400
    cleaned = [sanitize_text(i) for i in items if isinstance(i, str)]
    cleaned = [c for c in cleaned if c]
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400
    last_menu.extras = cleaned
    db.session.commit()
    return {"extras": cleaned}


def get_purchased() -> Union[Dict[str, List[str]], Tuple[Dict[str, str], int]]:
    """Return the latest weekly menu's checked-off grocery items (§13.3)."""
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400
    return {"purchased": list(last_menu.purchased or [])}


def set_purchased(items: List[str]) -> Union[Dict[str, List[str]], Tuple[Dict[str, str], int]]:
    """Replace the latest weekly menu's purchased-items list (§13.3)."""
    if not isinstance(items, list):
        return {"error": "purchased must be a list of strings"}, 400
    cleaned = [sanitize_text(i).lower() for i in items if isinstance(i, str)]
    cleaned = [c for c in cleaned if c]
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400
    last_menu.purchased = cleaned
    db.session.commit()
    return {"purchased": cleaned}


def toggle_purchased(item: str) -> Union[Dict[str, bool], Tuple[Dict[str, str], int]]:
    """Toggle a single item's checked-off state (§13.3).

    `item` is the normalized (lowercase) item name — the same key the frontend uses
    when it reads the `purchased` flag from `/grocery`.
    """
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400

    current: list = list(last_menu.purchased or [])
    norm = sanitize_text(item).lower()
    if not norm:
        return {"error": "Item name is required"}, 400

    if norm in current:
        current.remove(norm)
        state = False  # was removed → now unchecked
    else:
        current.append(norm)
        state = True  # was added → now checked

    last_menu.purchased = current
    db.session.commit()
    return {"item": norm, "purchased": state}


# §16.2 — store-layout category ordering (produce → meat → dairy → pantry → frozen → snacks → other)
_STORE_LAYOUT_ORDER: List[str] = [
    "Produce",
    "Protein",
    "Dairy",
    "Grains",
    "Snacks",
    "Other",
]


def _reorder_categories(grocery: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Reorder grocery dict keys to match a typical store layout (audit §16.2)."""
    ordered: Dict[str, List[Dict[str, Any]]] = {}
    ordered.update({k: grocery[k] for k in _STORE_LAYOUT_ORDER if k in grocery})
    for k in grocery:
        if k not in _STORE_LAYOUT_ORDER:
            ordered[k] = grocery[k]
    return ordered


def enhance_grocery_list() -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Build a grocery list, optionally enhanced by Ollama (§16.2).

    Runs the fast rule-based ``build_grocery_list()`` first.  If ``USE_OLLAMA`` is
    enabled, sends the list + week's meals to Ollama to (a) reorder categories
    into store-layout order and (b) suggest missing items.  On any Ollama error
    or timeout, returns the rule-based list unchanged.
    """
    result = build_grocery_list()
    if isinstance(result, tuple):
        return result  # propagate error: {"error": "Generate a menu first"}, 400

    if not current_app.config.get("USE_OLLAMA", False):
        return _reorder_categories(result)

    # gather week's meal ingredients for context
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    meal_ingredients: List[List[str]] = []
    if last_menu:
        for day, val in (last_menu.meals or {}).items():
            if isinstance(val, dict):
                meal = val
            elif isinstance(val, int):
                m = db.session.get(Meal, val)
                meal = m.to_dict() if m else {"ingredients": []}
            else:
                meal = {"ingredients": []}
            meal_ingredients.append(meal.get("ingredients") or [])

    # build a compact JSON-ish representation for the prompt
    list_text = json.dumps(
        {cat: [i["item"] for i in items] for cat, items in result.items()},
        indent=2,
    )
    meals_text = json.dumps(meal_ingredients, indent=2)
    prompt = (
        f"Here is a categorized grocery list with quantities (JSON, "
        f"{{category: [item strings]}}):\n{list_text}\n\n"
        f"Here are this week's planned meals' ingredients (JSON array):\n{meals_text}\n\n"
        f"Reorganize the categories into optimal store-layout order "
        f"(produce -> protein/meat -> dairy -> grains -> snacks -> other) and "
        f"suggest any ingredients that are missing based on the meals. If you suggest "
        f"new items, append them to the most appropriate existing category. "
        f"Return ONLY valid JSON in the same format: "
        f'{{"Produce": ["item1", "item2"], ...}}. '
        f"Keep the item names as-is (no quantities needed). Do not add commentary."
    )

    ollama_text = call_ollama(prompt, timeout=current_app.config.get("OLLAMA_TIMEOUT", 15))

    if ollama_text is None:
        return _reorder_categories(result)

    parsed = parse_json_list(ollama_text)
    # parse_json_list returns None for non-list; but we expect a dict here.
    # Re-parse as a dict if needed.
    if parsed is None:
        try:
            cleaned = ollama_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                cleaned = cleaned.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            parsed = None

    if not isinstance(parsed, dict):
        return _reorder_categories(result)

    # merge: keep rule-based item list, reorder, append AI-suggested new items
    merged: Dict[str, List[Dict[str, str]]] = {}
    for cat, items in parsed.items():
        if cat not in result:
            # brand-new category from Ollama — create it
            merged[cat] = []
        else:
            # preserve rule-based display (item, qty, purchased)
            merged[cat] = list(result[cat])
        for suggested in items:
            if not suggested:
                continue
            existing_names = {i["item"].lower() for i in merged[cat]}
            if suggested.lower() not in existing_names:
                merged[cat].append({"item": suggested.title(), "qty": "1", "purchased": False})

    # append any rules-based categories not touched by Ollama
    for cat, items in result.items():
        if cat not in merged:
            merged[cat] = list(items)

    return _reorder_categories(merged)
