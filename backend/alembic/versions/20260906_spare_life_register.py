"""spare life register

Revision ID: 20260906_spare_life
Revises: 20260823_stand_preparation_history
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260906_spare_life"
down_revision = "20260823_stand_preparation_history"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inventory_items", sa.Column("expected_life_hours", sa.Float(), nullable=True))
    op.add_column("inventory_items", sa.Column("observed_avg_life_hours", sa.Float(), nullable=True))
    op.add_column("inventory_items", sa.Column("reliability_pct", sa.Float(), nullable=True))
    op.add_column("inventory_items", sa.Column("availability_pct", sa.Float(), nullable=True))
    op.add_column("inventory_items", sa.Column("criticality", sa.String(length=20), nullable=False, server_default="MEDIUM"))
    op.add_column("inventory_items", sa.Column("used_at", sa.String(length=150), nullable=True))

    # Existing rows were historically stored as "SAP_CODE|Spare Name".
    # Keep only the human-readable spare name. If no separator exists, leave the name unchanged.
    op.execute("""
        UPDATE inventory_items
        SET name = btrim(split_part(name, '|', 2))
        WHERE position('|' in name) > 0
          AND btrim(split_part(name, '|', 2)) <> ''
    """)


def downgrade():
    op.drop_column("inventory_items", "used_at")
    op.drop_column("inventory_items", "criticality")
    op.drop_column("inventory_items", "availability_pct")
    op.drop_column("inventory_items", "reliability_pct")
    op.drop_column("inventory_items", "observed_avg_life_hours")
    op.drop_column("inventory_items", "expected_life_hours")
