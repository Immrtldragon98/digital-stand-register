"""Add stand-area integrity constraints.

Revision ID: 20260823_integrity
Revises: 20260823_optional_activity_user
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260823_integrity"
down_revision = "20260823_optional_activity_user"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_position_line_number",
        "positions",
        ["line_id", "position_number"],
    )
    op.create_check_constraint(
        "ck_position_number_1_10",
        "positions",
        "position_number >= 1 AND position_number <= 10",
    )
    op.create_unique_constraint(
        "uq_stand_assets_current_position_id",
        "stand_assets",
        ["current_position_id"],
    )
    op.create_unique_constraint(
        "uq_entry_guide_assets_current_position_id",
        "entry_guide_assets",
        ["current_position_id"],
    )
    op.create_index(
        "uq_active_stand_installation_position",
        "stand_installations",
        ["position_id"],
        unique=True,
        postgresql_where=sa.text("removed_at IS NULL"),
    )
    op.create_index(
        "uq_active_stand_installation_asset",
        "stand_installations",
        ["stand_id"],
        unique=True,
        postgresql_where=sa.text("removed_at IS NULL"),
    )
    op.create_index(
        "uq_active_entry_guide_position",
        "entry_guide_installations",
        ["position_id"],
        unique=True,
        postgresql_where=sa.text("removed_at IS NULL"),
    )
    op.create_index(
        "uq_active_entry_guide_asset",
        "entry_guide_installations",
        ["guide_id"],
        unique=True,
        postgresql_where=sa.text("removed_at IS NULL"),
    )


def downgrade():
    op.drop_index("uq_active_entry_guide_asset", table_name="entry_guide_installations")
    op.drop_index("uq_active_entry_guide_position", table_name="entry_guide_installations")
    op.drop_index("uq_active_stand_installation_asset", table_name="stand_installations")
    op.drop_index("uq_active_stand_installation_position", table_name="stand_installations")
    op.drop_constraint("uq_entry_guide_assets_current_position_id", "entry_guide_assets", type_="unique")
    op.drop_constraint("uq_stand_assets_current_position_id", "stand_assets", type_="unique")
    op.drop_constraint("ck_position_number_1_10", "positions", type_="check")
    op.drop_constraint("uq_position_line_number", "positions", type_="unique")
