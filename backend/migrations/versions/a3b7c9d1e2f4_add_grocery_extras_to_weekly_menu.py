"""add grocery `extras` JSON list to weekly_menu for user-added shopping items (audit B3a)

Revision ID: a3b7c9d1e2f4
Revises: 2d2d16ec2886
Create Date: 2026-08-07 02:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3b7c9d1e2f4'
down_revision = '2d2d16ec2886'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('weekly_menu', schema=None) as batch_op:
        batch_op.add_column(sa.Column('extras', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('weekly_menu', schema=None) as batch_op:
        batch_op.drop_column('extras')
