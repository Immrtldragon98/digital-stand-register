"""stand campaign events

Revision ID: 20260912_campaign_events
Revises: 20260909_components
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "20260912_campaign_events"
down_revision = "20260909_components"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stand_campaign_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stand_id", sa.Integer(), sa.ForeignKey("stand_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("installation_id", sa.Integer(), sa.ForeignKey("stand_installations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False, server_default="OBSERVATION"),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="LOW"),
        sa.Column("component_name", sa.String(length=100), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("action_taken", sa.Text(), nullable=True),
        sa.Column("event_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_by", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_campaign_events_stand_id", "stand_campaign_events", ["stand_id"])
    op.create_index("ix_campaign_events_installation_id", "stand_campaign_events", ["installation_id"])
    op.create_index("ix_campaign_events_event_at", "stand_campaign_events", ["event_at"])


def downgrade():
    op.drop_index("ix_campaign_events_event_at", table_name="stand_campaign_events")
    op.drop_index("ix_campaign_events_installation_id", table_name="stand_campaign_events")
    op.drop_index("ix_campaign_events_stand_id", table_name="stand_campaign_events")
    op.drop_table("stand_campaign_events")
