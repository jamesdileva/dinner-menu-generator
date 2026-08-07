"""Business logic for menu generation and daily picks (audit §4.1).

Kept free of Flask request/session coupling so it can be unit-tested in isolation.
All DB writes happen inside Flask request context (routes call these helpers).
"""

import random
from datetime import date

from models import Meal, WeeklyMenu, UsedMeal, db
from utils import fast_food_spots


def pick_takeout():
    """Quick Pick — pick a random takeout spot."""
    return random.choice(fast_food_spots)


def decide():
    """Quick Pick — random home OR takeout choice."""
    choice = random.choice(["home", "takeout"])

    if choice == "home":
        meals = Meal.query.all()
        if not meals:
            return {"error": "No meals available"}, 400

        meal = random.choice(meals)
        return {"mode": "home", "meal": meal.to_dict()}

    return {"mode": "takeout", "meal": random.choice(fast_food_spots)}


def pick_today():
    """`GET /menu/today` — random home meal, no repeats on the same calendar day.

    Persists its choice in `used_meal` so the no-repeat guarantee survives restarts
    (audit §3.9). Pruning stale rows from previous days is part of this operation.
    """
    meals = Meal.query.all()
    if not meals:
        return {"error": "No meals available"}, 400

    today = date.today().isoformat()

    # prune stale rows from previous days
    UsedMeal.query.filter(UsedMeal.date != today).delete()
    db.session.commit()

    used_ids = {u.meal_id for u in UsedMeal.query.filter_by(date=today).all()}
    available = [m for m in meals if m.id not in used_ids]

    # reset if we've used all meals today
    if not available:
        used_ids = set()
        available = meals

    meal = random.choice(available)

    db.session.add(UsedMeal(date=today, meal_id=meal.id))
    db.session.commit()

    return meal.to_dict()


def expand_menu(meals_map):
    """Resolve a WeeklyMenu's meals map into full meal dicts for display/export.

    Storage is now meal ids only (§5.13), but the API still returns expanded dicts so the
    frontend is unchanged. Also transparently handles legacy full-snapshot menus.
    """
    out = {}
    if not meals_map:
        return out
    for day, val in meals_map.items():
        if isinstance(val, dict):
            out[day] = val  # legacy full snapshot (already expanded)
        elif isinstance(val, int):
            m = db.session.get(Meal, val)
            out[day] = m.to_dict() if m else {"id": val, "name": None, "ingredients": []}
        else:
            out[day] = val
    return out


def list_menus():
    """`GET /menus` — all saved weekly menus for the history view (audit §5.15).

    Newest first. Each menu's meals are resolved from their stored ids (§5.13) so the
    history reflects the current Meal rows rather than stale snapshots.
    """
    menus = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).all()
    return [
        {"id": m.id, "meals": expand_menu(m.meals)}
        for m in menus
    ]


def _resolve_meal(val):
    """Turn a WeeklyMenu day value (meal id or full dict) into a Meal instance or None."""
    if isinstance(val, dict):
        return db.session.get(Meal, val.get("id"))
    if isinstance(val, int):
        return db.session.get(Meal, val)
    return None


def generate_week():
    """`GET /menu/week` — 7 distinct random meals (audit §5.13, §9.6).

    §9.6: pick 7 random meals at the DB level (`ORDER BY RANDOM() LIMIT 7`) instead of loading
    every meal into Python memory and calling `random.sample`. SQLite's `RANDOM()` returns
    distinct rows, so the no-internal-repeats guarantee holds; we guard on the count via a
    single COUNT query (no full table load). §5.13: store meal *ids*.
    """
    # single COUNT query — don't materialise the whole meals table just to count it
    if db.session.query(db.func.count()).select_from(Meal).scalar() < 7:
        return {"error": "Add at least 7 meals"}, 400

    selected = db.session.query(Meal).order_by(db.func.random()).limit(7).all()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    result = {days[i]: selected[i].id for i in range(7)}  # §5.13 store id, not snapshot

    menu = WeeklyMenu(meals=result)
    db.session.add(menu)
    db.session.commit()

    return result


def reroll_day(day):
    """`POST /menu/reroll/<day>` — swap one day in the most-recent weekly menu."""
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400

    meals = Meal.query.all()
    if not meals:
        return {"error": "No meals available"}, 400

    if day not in last_menu.meals:
        return {"error": f"Invalid day: {day}"}, 400

    # avoid the current meal for that day
    cur = _resolve_meal(last_menu.meals[day])  # §5.13 id-or-snapshot -> Meal
    current_meal_name = cur.name if cur else None
    available = [m for m in meals if m.name != current_meal_name]

    if not available:
        return {"error": "No other meals available"}, 400

    new_meal = random.choice(available)
    last_menu.meals[day] = new_meal.id  # §5.13 store id
    db.session.commit()

    return {
        "day": day,
        "meal": new_meal.to_dict()
    }


def set_menu_day(day, meal_dict):
    """`PUT /menu/<day>` — set the meal for a day in the last weekly menu.

    Used to (re)store a day's meal, e.g. to undo a reroll (audit §5.12).
    `meal_dict` should look like a meal's `to_dict()` output: {"id","name","ingredients"}.
    """
    last_menu = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).first()
    if not last_menu:
        return {"error": "Generate a menu first"}, 400

    if day not in last_menu.meals:
        return {"error": f"Invalid day: {day}"}, 400

    # §5.13 store the meal id; accept either a full meal dict (undo payload) or a bare id
    meal_id = meal_dict["id"] if isinstance(meal_dict, dict) else meal_dict
    last_menu.meals[day] = meal_id
    db.session.commit()

    meal = db.session.get(Meal, meal_id)
    if meal:
        return {"day": day, "meal": meal.to_dict()}
    if isinstance(meal_dict, dict):
        return {"day": day, "meal": meal_dict}
    return {"day": day, "meal": {"id": meal_id, "name": None, "ingredients": []}}
