"""stand running condition flags

Revision ID: 20260912_condition_flags
Revises: 20260912_campaign_events
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "20260912_condition_flags"
down_revision = "20260912_campaign_events"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stand_assets", sa.Column("abnormal_sound", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade():
    op.drop_column("stand_assets", "abnormal_sound")
