"""reliability foundation and historical data

Revision ID: 20260906_reliability
Revises: 20260906_knowledge_docs
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260906_reliability"
down_revision = "20260906_knowledge_docs"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("positions", sa.Column("target_life_hours", sa.Float(), nullable=True))

    op.create_table(
        "historical_campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("line_name", sa.String(length=10), nullable=False),
        sa.Column("position_number", sa.Integer(), nullable=False),
        sa.Column("stand_code", sa.String(length=50), nullable=False),
        sa.Column("installed_date", sa.Date(), nullable=False),
        sa.Column("removed_date", sa.Date(), nullable=True),
        sa.Column("life_days", sa.Float(), nullable=True),
        sa.Column("removal_reason", sa.Text(), nullable=True),
        sa.Column("inferred", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("source_file", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source_file", "line_name", "position_number", "stand_code", "installed_date", name="uq_historical_campaign"),
    )
    op.create_index("ix_historical_campaigns_line_name", "historical_campaigns", ["line_name"])
    op.create_index("ix_historical_campaigns_position_number", "historical_campaigns", ["position_number"])
    op.create_index("ix_historical_campaigns_stand_code", "historical_campaigns", ["stand_code"])

    op.create_table(
        "historical_spare_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("spare_name", sa.String(length=150), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source_file", "usage_date", "spare_name", name="uq_historical_spare_usage"),
    )
    op.create_index("ix_historical_spare_usage_usage_date", "historical_spare_usage", ["usage_date"])
    op.create_index("ix_historical_spare_usage_spare_name", "historical_spare_usage", ["spare_name"])

    op.create_table(
        "process_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("shift", sa.String(length=20), nullable=True),
        sa.Column("source_wrm", sa.Integer(), nullable=False),
        sa.Column("line_name", sa.String(length=10), nullable=False),
        sa.Column("coil_no", sa.String(length=80), nullable=True),
        sa.Column("uts_band", sa.String(length=30), nullable=True),
        sa.Column("casting_speed", sa.Float(), nullable=True),
        sa.Column("emulsion_temp", sa.Float(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source_file", "line_name", "observation_date", "shift", "coil_no", name="uq_process_observation"),
    )
    op.create_index("ix_process_observations_observation_date", "process_observations", ["observation_date"])
    op.create_index("ix_process_observations_line_name", "process_observations", ["line_name"])
    op.create_index("ix_process_observations_coil_no", "process_observations", ["coil_no"])


def downgrade():
    op.drop_index("ix_process_observations_coil_no", table_name="process_observations")
    op.drop_index("ix_process_observations_line_name", table_name="process_observations")
    op.drop_index("ix_process_observations_observation_date", table_name="process_observations")
    op.drop_table("process_observations")
    op.drop_index("ix_historical_spare_usage_spare_name", table_name="historical_spare_usage")
    op.drop_index("ix_historical_spare_usage_usage_date", table_name="historical_spare_usage")
    op.drop_table("historical_spare_usage")
    op.drop_index("ix_historical_campaigns_stand_code", table_name="historical_campaigns")
    op.drop_index("ix_historical_campaigns_position_number", table_name="historical_campaigns")
    op.drop_index("ix_historical_campaigns_line_name", table_name="historical_campaigns")
    op.drop_table("historical_campaigns")
    op.drop_column("positions", "target_life_hours")
