"""SQLAlchemy models + shared db instance (audit §4.1).

`db` is constructed *without* an app so this module has no dependency on the Flask
application object — `app.py` calls `db.init_app(app)` at startup. This breaks the
circular import that would otherwise form (routes → models → app → routes).
"""

from typing import Any, Dict

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SavedGrocery(db.Model):
    """Persistent grocery catalog items (§13.3b → renamed from Snack → SavedGrocery).

    Unlike weekly extras (free-text strings on ``WeeklyMenu.extras``), saved groceries
    are a persistent catalog the user can pick from across weeks.  Any ad-hoc extra can
    be promoted to a saved grocery — snacks, staples, condiments, anything.

    The ``group`` column distinguishes snacks from staples for UI grouping.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    # §13.3b — group for UI sectioning: "snacks" (matches _SNACKS_WORDS aisle) vs
    # "staples" (everything else). Defaults to "staples" for legacy entries.
    group = db.Column(db.String(20), nullable=False, default="staples")
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "group": self.group}


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ingredients = db.Column(db.JSON)
    category = db.Column(db.String(50))  # audit §5.14: optional meal category/tag

    # audit §9.1 — indexes for the frequently-run queries: the paginated, ordered `/meals`
    # list (order by name) and the §5.14 category filter + `/meals/categories` distinct
    # query. (A functional `lower(name)` CI index is skipped: SQLite/Alembic can't reflect
    # expression indexes for autogenerate, and the dedupe lookups below run on a small local
    # table where the overhead isn't worth a hand-managed raw-SQL index.)
    __table_args__ = (
        db.Index("ix_meal_name", "name"),
        db.Index("ix_meal_category", "category"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients,
            "category": self.category,
        }


class WeeklyMenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meals = db.Column(db.JSON)
    # audit B3a — user-added grocery items (e.g. "oreos", "milk") not tied to a meal,
    # attached to the week this menu represents so they flow into /grocery + exports.
    extras = db.Column(db.JSON, nullable=True, default=lambda: [])
    # §13.3 — item names the user has checked off the grocery list for this week.
    # Stored as the *normalized* item key produced by INGREDIENT_MAP (same key used in
    # build_grocery_list's grocery_totals dict), so it stays consistent across meal-derived
    # ingredients and user-added extras.
    purchased = db.Column(db.JSON, nullable=True, default=lambda: [])


class UsedMeal(db.Model):
    """One row per home-meal picked on a given day (audit §3.9 — persists across restarts)."""

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))  # YYYY-MM-DD
    meal_id = db.Column(db.Integer)

    # audit §9.1 — index the column pick_today() prunes/queries by (date).
    __table_args__ = (db.Index("ix_used_meal_date", "date"),)
