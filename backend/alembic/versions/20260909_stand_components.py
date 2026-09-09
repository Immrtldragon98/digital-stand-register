"""stand component preparation

Revision ID: 20260909_components
Revises: 20260906_reliability
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

revision = "20260909_components"
down_revision = "20260906_reliability"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stand_component_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("required_qty", sa.Integer(), nullable=True),
        sa.Column("even_position_extra", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expected_life_hours", sa.Float(), nullable=True),
        sa.Column("criticality", sa.String(length=16), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "stand_component_preparations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stand_id", sa.Integer(), sa.ForeignKey("stand_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="SAVED"),
        sa.Column("prepared_by", sa.String(length=100), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_stand_component_preparations_stand_id", "stand_component_preparations", ["stand_id"])
    op.create_table(
        "stand_component_preparation_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("preparation_id", sa.Integer(), sa.ForeignKey("stand_component_preparations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_type_id", sa.Integer(), sa.ForeignKey("stand_component_types.id"), nullable=False),
        sa.Column("new_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reused_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("carried_life_hours", sa.Float(), nullable=True),
    )
    op.create_index("ix_stand_component_items_preparation_id", "stand_component_preparation_items", ["preparation_id"])
    op.create_index("ix_stand_component_items_component_type_id", "stand_component_preparation_items", ["component_type_id"])

    components = [
        ("Oil Seal", 6, False),
        ("Top Gasket", 3, False),
        ("Coupler", 1, False),
        ("Special Bearing", 6, False),
        ("O-Ring", 6, False),
        ("Primary Shaft", 1, False),
        ("Secondary Shaft", 2, False),
        ("Roll", 3, False),
        ("Hub", 3, False),
        ("Hub Speed Sleeve", 6, False),
        ("Bevel Gear", 6, False),
        ("Coupler Speedi Sleeve", 1, False),
        ("Entry Guide Roll", None, True),
    ]
    table = sa.table(
        "stand_component_types",
        sa.column("name", sa.String),
        sa.column("required_qty", sa.Integer),
        sa.column("even_position_extra", sa.Boolean),
        sa.column("active", sa.Boolean),
    )
    op.bulk_insert(table, [
        {"name": name, "required_qty": qty, "even_position_extra": even, "active": True}
        for name, qty, even in components
    ])


def downgrade():
    op.drop_index("ix_stand_component_items_component_type_id", table_name="stand_component_preparation_items")
    op.drop_index("ix_stand_component_items_preparation_id", table_name="stand_component_preparation_items")
    op.drop_table("stand_component_preparation_items")
    op.drop_index("ix_stand_component_preparations_stand_id", table_name="stand_component_preparations")
    op.drop_table("stand_component_preparations")
    op.drop_table("stand_component_types")
