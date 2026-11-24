"""Atomic write receipts."""
from alembic import op
import sqlalchemy as sa
revision = '20261124_command_receipts'
down_revision = '20261124_component_lifecycle'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('command_receipts', sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('request_key',sa.String(128),nullable=False),sa.Column('request_hash',sa.String(64),nullable=False),
        sa.Column('scope',sa.String(100),nullable=False),sa.Column('response',sa.JSON(),nullable=True),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.UniqueConstraint('user_id','request_key',name='uq_command_user_key'))

def downgrade():
    raise RuntimeError('Receipts are audit evidence; restore backup for downgrade.')
