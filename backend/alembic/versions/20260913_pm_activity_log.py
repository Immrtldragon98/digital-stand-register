"""Extend PM activities into maintenance activity log
Revision ID: 20260913_pm_activity_log
Revises: 20260912_pm_activities
"""
from alembic import op
import sqlalchemy as sa
revision="20260913_pm_activity_log"
down_revision="20260912_pm_activities"
branch_labels=None
depends_on=None
def upgrade():
    for name,typ in [
      ("shift",sa.String(8)),("position_number",sa.Integer()),("stand_code",sa.String(50)),
      ("component",sa.String(100)),("activity_type",sa.String(60)),("from_value",sa.String(100)),
      ("to_value",sa.String(100)),("source_text",sa.Text())]:
        op.add_column("pm_activities",sa.Column(name,typ,nullable=True))
def downgrade():
    for n in ["source_text","to_value","from_value","activity_type","component","stand_code","position_number","shift"]:
        op.drop_column("pm_activities",n)
