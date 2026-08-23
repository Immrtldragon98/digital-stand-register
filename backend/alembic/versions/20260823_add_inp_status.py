"""preserve INP status from the 22/08/2026 report

Revision ID: 20260823_inp_status
Revises: 20260823_prep_history
"""
from alembic import op

revision = "20260823_inp_status"
down_revision = "20260823_prep_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL supports adding enum values in-place. IF NOT EXISTS keeps this
    # commissioning migration safe if a DBA created the value manually first.
    op.execute("ALTER TYPE statusenum ADD VALUE IF NOT EXISTS 'INP' AFTER 'PENDING'")


def downgrade() -> None:
    # PostgreSQL does not support dropping an enum value in-place. Leaving INP
    # present is safer than rebuilding a production enum during downgrade.
    pass
