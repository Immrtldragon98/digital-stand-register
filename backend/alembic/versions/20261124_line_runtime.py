"""Measured line running-state ledger; historical life remains unverified."""
from alembic import op
import sqlalchemy as sa
revision='20261124_line_runtime'
down_revision='20261123_spare_life'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('line_runtime_events', sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('line_id',sa.Integer(),sa.ForeignKey('lines.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('state',sa.String(10),nullable=False),sa.Column('event_at',sa.DateTime(),nullable=False),
        sa.Column('recorded_by',sa.String(100),nullable=False),sa.Column('reason',sa.String(500)),
        sa.CheckConstraint("state IN ('RUNNING','STOPPED')",name='ck_line_runtime_state'),
        sa.UniqueConstraint('line_id','event_at',name='uq_line_runtime_at'))
    op.create_index('ix_line_runtime_events_line_id','line_runtime_events',['line_id'])
    op.create_index('ix_line_runtime_events_event_at','line_runtime_events',['event_at'])

def downgrade():
    raise RuntimeError('Runtime history cannot be discarded by downgrade; restore a reviewed backup.')
