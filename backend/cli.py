"""Maintenance CLI commands for the Dinner Menu Generator (audit §5.5 / §5.6 / §8.1).

These used to be publicly reachable HTTP routes on `application.db`. That was a
maintenance/ops surface accidentally exposed in production builds (the PyInstaller
executable). They are now **CLI-only** — run from the backend dir:

    python -m flask --app app init-db   # create tables (idempotent)
    python -m flask --app app fix-data  # cleanse/normalise meals + dedupe

The frozen exe is unaffected: it calls `flask db upgrade` at startup (app.py) to
provision tables, and neither operation is exposed over HTTP any more, so an external
party can no longer wipe/cleanse data via the running server.

`/import-file` is intentionally *not* moved here: per §5.4 it is the user-facing data
import feature (additive + deduping, non-destructive), so it remains an HTTP endpoint.
"""

import click
from flask.cli import with_appcontext

from models import db, Meal
from utils import generate_ingredients, normalize_ingredients, clean_meal_name


def init_db_tables():
    db.create_all()


def cleanse_meals():
    """Backfill missing ingredients, normalise existing ones, and drop duplicate meals."""
    meals = Meal.query.all()
    seen = set()

    for meal in meals:
        combined = " ".join(meal.ingredients) if meal.ingredients else ""

        # backfill if empty
        if not combined.strip():
            meal.ingredients = generate_ingredients(meal.name)
        else:
            meal.ingredients = normalize_ingredients(combined)

        cleaned_name = clean_meal_name(meal.name)
        normalized = cleaned_name.lower()

        # remove duplicates
        if normalized in seen:
            db.session.delete(meal)
            continue

        seen.add(normalized)
        meal.name = cleaned_name

    db.session.commit()


@click.command("init-db")
@with_appcontext
def init_db():
    """Create database tables (idempotent)."""
    init_db_tables()
    click.echo("DB initialized")


@click.command("fix-data")
@with_appcontext
def fix_data():
    """Cleanse/normalise meals in place: backfill ingredients, normalise, dedupe."""
    cleanse_meals()
    click.echo("Data fully cleaned!")


def register_cli(app):
    app.cli.add_command(init_db)
    app.cli.add_command(fix_data)
