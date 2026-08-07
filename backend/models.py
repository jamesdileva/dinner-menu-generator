"""SQLAlchemy models + shared db instance (audit §4.1).

`db` is constructed *without* an app so this module has no dependency on the Flask
application object — `app.py` calls `db.init_app(app)` at startup. This breaks the
circular import that would otherwise form (routes → models → app → routes).
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ingredients = db.Column(db.JSON)
    category = db.Column(db.String(50))  # audit §5.14: optional meal category/tag

    # audit §9.1 — indexes for the frequently-run queries: the paginated, ordered `/meals`
    # list (order by name) and the §5.14 category filter + `/meals/categories` distinct
    # query. (A functional `lower(name)` CI index is skipped: SQLite/Alembic can't reflect
    # expression indexes for autogenerate, and the dedupe lookups below run on a small local
    # table where the overhead isn't worth a hand-maintained raw-SQL index.)
    __table_args__ = (
        db.Index("ix_meal_name", "name"),
        db.Index("ix_meal_category", "category"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients,
            "category": self.category
        }


class WeeklyMenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meals = db.Column(db.JSON)
    # audit B3a — user-added grocery items (e.g. "oreos", "milk") not tied to a meal,
    # attached to the week this menu represents so they flow into /grocery + exports.
    extras = db.Column(db.JSON, nullable=True, default=lambda: [])


class UsedMeal(db.Model):
    """One row per home-meal picked on a given day (audit §3.9 — persists across restarts)."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))   # YYYY-MM-DD
    meal_id = db.Column(db.Integer)

    # audit §9.1 — index the column pick_today() prunes/queries by (date).
    __table_args__ = (db.Index("ix_used_meal_date", "date"),)
