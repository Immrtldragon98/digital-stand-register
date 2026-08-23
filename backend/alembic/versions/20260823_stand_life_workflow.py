"""Stand life, preparation workflow, entry-guide history, stand changes.

Revision ID: 20260823standlife
Revises: 967dbde99978
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260823standlife"
down_revision: Union[str, Sequence[str], None] = "967dbde99978"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enums are recreated because the workflow has materially changed.
    op.execute("ALTER TYPE statusenum RENAME TO statusenum_old")
    statusenum = sa.Enum("YET_TO_READY", "PENDING", "GAUGING", "HYDROTEST", "READY", "INSTALLED", name="statusenum")
    statusenum.create(op.get_bind(), checkfirst=False)

    for table in ("stand_assets", "entry_guide_assets"):
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN current_status TYPE statusenum "
            f"USING (CASE current_status::text "
            f"WHEN 'MAINTENANCE' THEN 'PENDING' "
            f"ELSE current_status::text END)::statusenum"
        )
    op.execute("DROP TYPE statusenum_old")

    op.add_column("stand_assets", sa.Column("lifetime_hours", sa.Float(), nullable=False, server_default="0"))
    op.add_column("stand_assets", sa.Column("leakage", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("stand_assets", sa.Column("vibration", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("stand_assets", sa.Column("condition_notes", sa.String(length=500), nullable=True))

    guidecondition = sa.Enum("NEW", "OLD", name="entryguideconditionenum")
    guidecondition.create(op.get_bind(), checkfirst=True)
    op.add_column("entry_guide_assets", sa.Column("condition", guidecondition, nullable=False, server_default="OLD"))
    op.add_column("entry_guide_assets", sa.Column("lifetime_hours", sa.Float(), nullable=False, server_default="0"))
    op.add_column("entry_guide_assets", sa.Column("condition_notes", sa.String(length=500), nullable=True))

    for table in ("stand_installations", "entry_guide_installations"):
        op.add_column(table, sa.Column("installed_by", sa.String(length=100), nullable=True))
        op.add_column(table, sa.Column("removed_by", sa.String(length=100), nullable=True))
        op.add_column(table, sa.Column("removal_reason", sa.String(length=500), nullable=True))
        op.add_column(table, sa.Column("campaign_hours", sa.Float(), nullable=True))

    op.create_table(
        "stand_change_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("position_id", sa.Integer(), nullable=False),
        sa.Column("removed_stand_id", sa.Integer(), nullable=False),
        sa.Column("installed_stand_id", sa.Integer(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("changed_by", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("removed_condition", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"]),
        sa.ForeignKeyConstraint(["removed_stand_id"], ["stand_assets.id"]),
        sa.ForeignKeyConstraint(["installed_stand_id"], ["stand_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stand_change_events_id"), "stand_change_events", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_stand_change_events_id"), table_name="stand_change_events")
    op.drop_table("stand_change_events")
    for table in ("stand_installations", "entry_guide_installations"):
        op.drop_column(table, "campaign_hours")
        op.drop_column(table, "removal_reason")
        op.drop_column(table, "removed_by")
        op.drop_column(table, "installed_by")
    op.drop_column("entry_guide_assets", "condition_notes")
    op.drop_column("entry_guide_assets", "lifetime_hours")
    op.drop_column("entry_guide_assets", "condition")
    sa.Enum(name="entryguideconditionenum").drop(op.get_bind(), checkfirst=True)
    op.drop_column("stand_assets", "condition_notes")
    op.drop_column("stand_assets", "vibration")
    op.drop_column("stand_assets", "leakage")
    op.drop_column("stand_assets", "lifetime_hours")
