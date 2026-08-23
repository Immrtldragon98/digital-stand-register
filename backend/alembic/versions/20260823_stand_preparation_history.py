"""add stand preparation history

Revision ID: 20260823_prep_history
Revises: 20260823_inventory_history
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260823_prep_history"
down_revision = "20260823_inventory_history"
branch_labels = None
depends_on = None


def upgrade():
    status_enum = postgresql.ENUM(
        "YET_TO_READY", "PENDING", "GAUGING", "HYDROTEST", "READY", "INSTALLED",
        name="statusenum", create_type=False
    )
    op.create_table(
        "stand_preparation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stand_id", sa.Integer(), nullable=False),
        sa.Column("from_status", status_enum, nullable=False),
        sa.Column("to_status", status_enum, nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=False),
        sa.Column("remarks", sa.String(length=500), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["stand_id"], ["stand_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stand_preparation_events_id"), "stand_preparation_events", ["id"], unique=False)
    op.create_index(op.f("ix_stand_preparation_events_stand_id"), "stand_preparation_events", ["stand_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_stand_preparation_events_stand_id"), table_name="stand_preparation_events")
    op.drop_index(op.f("ix_stand_preparation_events_id"), table_name="stand_preparation_events")
    op.drop_table("stand_preparation_events")
