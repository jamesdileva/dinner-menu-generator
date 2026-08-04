"""Business logic for grocery-list generation (audit §4.1).

Ports the aggregation/quantity-parsing/categorisation that lived inline in the
`GET /grocery` route. Pure DB reads here; the route just calls `build_grocery_list()`.
"""

import re

from models import WeeklyMenu
from utils import INGREDIENT_MAP, parse_quantity, categorize_ingredient, pluralize_word


# common units to intercept while parsing ingredient strings
UNIT_PATTERN = re.compile(
    r"\b(lb|lbs|can|cans|oz|ozs|tsp|tbsp|cup|cups|pack|g|kg|piece|pieces)\b"
)


def build_grocery_list():
    """Build a categorised grocery list from the most-recent weekly menu.

    Returns `({"Protein": [{"item": ..., "qty": ...}], ...})` or an error tuple
    `(error_dict, status_code)`.
    """
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400

    # Structure: { "ingredient_name": { "unit_type": total_quantity } }
    grocery_totals = {}

    for day, meal in last_menu.meals.items():
        if not meal.get("ingredients"):
            continue

        for raw_item in meal["ingredients"]:
            if not raw_item:
                continue

            # 1. clean & apply ingredient map
            cleaned_str = raw_item.lower().strip()

            # 2. parse quantity + units
            qty = 1.0          # default multiplier
            unit = "count"     # default unit if none found

            num_match = re.match(r"^([0-9\./\s]+)", cleaned_str)
            if num_match:
                num_str = num_match.group(1).strip()
                qty = parse_quantity(num_str)
                # strip numbers from the string
                cleaned_str = cleaned_str[num_match.end():].strip()

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

    # 4. group by category
    grouped = {}
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

            grouped[category].append({
                "item": item_display,
                "qty": qty_str
            })

    return grouped
