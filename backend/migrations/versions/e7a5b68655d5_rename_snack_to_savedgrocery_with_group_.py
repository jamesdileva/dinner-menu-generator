"""rename Snack to SavedGrocery with group column (§13.3b)

Revision ID: e7a5b68655d5
Revises: 161ee7d4a387
Create Date: 2026-08-08 23:05:08.600716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7a5b68655d5'
down_revision = '161ee7d4a387'
branch_labels = None
depends_on = None


def upgrade():
    # §13.3b — rename 'snack' table to 'saved_grocery', add 'group' column.
    # Use batch mode for SQLite compatibility (rename + add column in one op).
    with op.batch_alter_table("snack", schema=None) as batch_op:
        batch_op.alter_column("name")  # no-op, keeps the column reference valid
        batch_op.add_column(sa.Column("group", sa.String(length=20), nullable=False, server_default="staples"))

    # Rename the table
    op.rename_table("snack", "saved_grocery")

    # Recreate the index with the new name
    with op.batch_alter_table("saved_grocery", schema=None) as batch_op:
        batch_op.drop_index("ix_snack_name")
        batch_op.create_index("ix_saved_grocery_name", ["name"], unique=True)


def downgrade():
    with op.batch_alter_table("saved_grocery", schema=None) as batch_op:
        batch_op.drop_index("ix_saved_grocery_name")

    op.rename_table("saved_grocery", "snack")

    with op.batch_alter_table("snack", schema=None) as batch_op:
        batch_op.drop_column("group")
        batch_op.create_index("ix_snack_name", ["name"], unique=True)
