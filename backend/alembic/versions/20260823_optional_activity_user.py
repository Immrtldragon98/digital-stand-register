"""allow operator-only plant activity logs

Revision ID: 20260823_optional_activity_user
Revises: 20260823_stand_life_workflow
Create Date: 2026-08-23
"""
from alembic import op

revision = "20260823_optional_activity_user"
down_revision = "20260823standlife"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.alter_column("user_id", nullable=True)


def downgrade():
    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.alter_column("user_id", nullable=False)
