"""add inventory transaction history and archive support

Revision ID: 20260823_inventory_history
Revises: 20260823_inventory
"""
from alembic import op
import sqlalchemy as sa

revision = "20260823_inventory_history"
down_revision = "20260823_inventory"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_items",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_inventory_items_is_active", "inventory_items", ["is_active"], unique=False)

    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity_before", sa.Integer(), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("operator", sa.String(length=150), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_inventory_transactions_id", "inventory_transactions", ["id"], unique=False)
    op.create_index("ix_inventory_transactions_item_id", "inventory_transactions", ["item_id"], unique=False)
    op.create_index("ix_inventory_transactions_created_at", "inventory_transactions", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_inventory_transactions_created_at", table_name="inventory_transactions")
    op.drop_index("ix_inventory_transactions_item_id", table_name="inventory_transactions")
    op.drop_index("ix_inventory_transactions_id", table_name="inventory_transactions")
    op.drop_table("inventory_transactions")
    op.drop_index("ix_inventory_items_is_active", table_name="inventory_items")
    op.drop_column("inventory_items", "is_active")
