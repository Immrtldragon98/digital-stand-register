"""Merge retired Unstarted stand status into Pending, preserving history."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_pending_stands"
down_revision = "20260913_pm_activity_log"
branch_labels = None
depends_on = None


def upgrade():
    # Keep the legacy enum value for historical preparation events only.
    op.execute(sa.text("""
        INSERT INTO stand_preparation_events
            (stand_id, from_status, to_status, updated_by, remarks, changed_at)
        SELECT id, current_status, 'PENDING', 'System',
               'Unstarted stage retired; moved to Pending.', CURRENT_TIMESTAMP
        FROM stand_assets WHERE current_status = 'YET_TO_READY'
    """))
    op.execute(sa.text("""
        UPDATE stand_assets SET current_status = 'PENDING', current_location = 'WIP'
        WHERE current_status = 'YET_TO_READY'
    """))
    with op.batch_alter_table("stand_assets") as batch:
        batch.create_check_constraint("ck_stand_no_unstarted", "current_status <> 'YET_TO_READY'")


def downgrade():
    with op.batch_alter_table("stand_assets") as batch:
        batch.drop_constraint("ck_stand_no_unstarted", type_="check")
    # Do not reverse real preparation work or erase the migration audit events.
