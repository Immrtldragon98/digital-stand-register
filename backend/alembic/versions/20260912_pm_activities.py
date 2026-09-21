"""PM schedule activities
Revision ID: 20260912_pm_activities
Revises: 20260912_campaign_events
"""
from alembic import op
import sqlalchemy as sa
revision="20260912_pm_activities"
down_revision="20260912_condition_flags"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("pm_activities",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("planned_date",sa.Date(),nullable=False),sa.Column("line_name",sa.String(16),nullable=True),sa.Column("equipment",sa.String(120),nullable=False),sa.Column("activity",sa.String(255),nullable=False),sa.Column("frequency",sa.String(40),nullable=True),sa.Column("assigned_to",sa.String(100),nullable=True),sa.Column("status",sa.String(20),nullable=False,server_default="PLANNED"),sa.Column("completed_date",sa.Date(),nullable=True),sa.Column("remarks",sa.Text(),nullable=True),sa.Column("created_by",sa.String(100),nullable=False),sa.Column("updated_by",sa.String(100),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("updated_at",sa.DateTime(),nullable=False))
    op.create_index("ix_pm_activities_planned_date","pm_activities",["planned_date"])
    op.create_index("ix_pm_activities_line_name","pm_activities",["line_name"])
    op.create_index("ix_pm_activities_status","pm_activities",["status"])

def downgrade():
    op.drop_table("pm_activities")
