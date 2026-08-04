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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients
        }


class WeeklyMenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meals = db.Column(db.JSON)


class UsedMeal(db.Model):
    """One row per home-meal picked on a given day (audit §3.9 — persists across restarts)."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))   # YYYY-MM-DD
    meal_id = db.Column(db.Integer)
