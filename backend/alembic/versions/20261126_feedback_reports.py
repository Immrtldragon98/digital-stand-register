"""Private bug and suggestion inbox, with durable retry keys."""
from alembic import op
import sqlalchemy as sa

revision = '20261126_feedback_reports'
down_revision = '20261124_command_receipts'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('feedback_reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('request_id', sa.String(36), nullable=False),
        sa.Column('kind', sa.String(16), nullable=False),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('page', sa.String(200), nullable=False, server_default=''),
        sa.Column('reporter', sa.String(80), nullable=False, server_default=''),
        sa.Column('client_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='OPEN'),
        sa.Column('admin_notes', sa.Text(), nullable=False, server_default=''),
        sa.Column('updated_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('request_id', name='uq_feedback_request'),
        sa.CheckConstraint("kind IN ('BUG','SUGGESTION')", name='ck_feedback_kind'),
        sa.CheckConstraint("status IN ('OPEN','IN_PROGRESS','RESOLVED','DECLINED')", name='ck_feedback_status'))
    op.create_index('ix_feedback_reports_status', 'feedback_reports', ['status'])
    op.create_index('ix_feedback_client_created', 'feedback_reports', ['client_hash','created_at'])


def downgrade():
    raise RuntimeError('Feedback history must be preserved; restore a reviewed backup for rollback.')
