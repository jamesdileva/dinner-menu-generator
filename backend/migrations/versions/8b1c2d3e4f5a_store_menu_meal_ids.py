"""store meal ids in weekly menus instead of full snapshots (audit §5.13)

Previously `WeeklyMenu.meals` stored a full meal dict per day (name + ingredients) so
that editing a meal never reflected in past menus. This migration rewrites every stored
menu to reference meals by `id` (the ingredients/name are resolved live at read time via
`menu_service.expand_menu` / `grocery_service`). The API shape returned to clients is
unchanged (still full meal dicts), so the frontend needs no changes.

Revision ID: 8b1c2d3e4f5a
Revises: 7a9c4f2e1b86
Create Date: 2026-08-05

"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b1c2d3e4f5a'
down_revision = '7a9c4f2e1b86'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # Raw text() select returns the SQLite TEXT storage of the JSON column, so parse
    # defensively. Each day value becomes either an integer meal id (new) or is left as-is
    # if it is already an id / non-dict.
    rows = bind.execute(sa.text("SELECT id, meals FROM weekly_menu")).fetchall()
    for row in rows:
        raw = row[1]
        meals = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(meals, dict):
            continue
        new_meals = {}
        for day, val in meals.items():
            if isinstance(val, dict) and "id" in val:
                new_meals[day] = val["id"]
            elif isinstance(val, int):
                new_meals[day] = val
            else:
                new_meals[day] = None
        bind.execute(
            sa.text("UPDATE weekly_menu SET meals = :m WHERE id = :id"),
            {"m": json.dumps(new_meals), "id": row[0]},
        )


def downgrade():
    # One-way data migration: the dropped ingredient snapshots cannot be reconstructed.
    pass
