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


def generate_week():
    """`GET /menu/week` — 7 distinct meals (random.sample), stored as a snapshot."""
    meals = Meal.query.all()

    if len(meals) < 7:
        return {"error": "Add at least 7 meals"}, 400

    selected = random.sample(meals, 7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    result = {
        days[i]: selected[i].to_dict()
        for i in range(7)
    }

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

    # avoid the current meal for that day
    current_meal_name = last_menu.meals[day]["name"]
    available = [m for m in meals if m.name != current_meal_name]

    if not available:
        return {"error": "No other meals available"}, 400

    new_meal = random.choice(available)
    last_menu.meals[day] = new_meal.to_dict()
    db.session.commit()

    return {
        "day": day,
        "meal": new_meal.to_dict()
    }
