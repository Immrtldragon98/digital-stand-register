"""add editable inventory

Revision ID: 20260823_inventory
Revises: 20260823_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260823_inventory"
down_revision = "20260823_integrity"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minimum_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location", sa.String(length=150), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_inventory_items_name", "inventory_items", ["name"], unique=True)

def downgrade():
    op.drop_index("ix_inventory_items_name", table_name="inventory_items")
    op.drop_table("inventory_items")
