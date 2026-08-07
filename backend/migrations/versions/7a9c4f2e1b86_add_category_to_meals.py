"""add category column to Meal (audit §5.14)

Revision ID: 7a9c4f2e1b86
Revises: 6c296b498bf1
Create Date: 2026-08-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a9c4f2e1b86'
down_revision = '6c296b498bf1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('meal', sa.Column('category', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('meal', 'category')
