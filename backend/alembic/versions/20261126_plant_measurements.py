"""Evidence for preparation elapsed time, maintenance value and shift confirmations."""
from alembic import op
import sqlalchemy as sa
revision = '20261126_plant_measurements'
down_revision = '20261126_feedback_reports'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('preparation_cycles', sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('stand_id',sa.Integer(),sa.ForeignKey('stand_assets.id'),nullable=False),
        sa.Column('started_at',sa.DateTime(),nullable=False),sa.Column('started_by',sa.String(100),nullable=False),
        sa.Column('finished_at',sa.DateTime()),sa.Column('finished_by',sa.String(100)))
    op.create_index('ix_preparation_cycles_stand_id','preparation_cycles',['stand_id'])
    op.create_index('uq_open_preparation_cycle','preparation_cycles',['stand_id'],unique=True,postgresql_where=sa.text('finished_at IS NULL'))
    op.create_table('maintenance_measurements',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('request_id',sa.String(36),nullable=False,unique=True),sa.Column('kind',sa.String(24),nullable=False),
        sa.Column('duration_minutes',sa.Float()),sa.Column('description',sa.Text(),nullable=False),
        sa.Column('stand_id',sa.Integer(),sa.ForeignKey('stand_assets.id')),sa.Column('item_id',sa.Integer(),sa.ForeignKey('inventory_items.id')),
        sa.Column('recorded_by',sa.String(100),nullable=False),sa.Column('recorded_at',sa.DateTime(),nullable=False))
    op.create_index('ix_maintenance_measurements_recorded_at','maintenance_measurements',['recorded_at'])
    op.create_table('value_baselines',sa.Column('metric',sa.String(40),primary_key=True),sa.Column('value',sa.Float(),nullable=False),
        sa.Column('sample_count',sa.Integer(),nullable=False),sa.Column('period_start',sa.Date(),nullable=False),sa.Column('period_end',sa.Date(),nullable=False),
        sa.Column('source',sa.String(500),nullable=False),sa.Column('recorded_by',sa.String(100),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False))
    op.create_table('runtime_confirmations',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('line_id',sa.Integer(),sa.ForeignKey('lines.id'),nullable=False),sa.Column('state',sa.String(10),nullable=False),
        sa.Column('confirmed_at',sa.DateTime(),nullable=False),sa.Column('confirmed_by',sa.String(100),nullable=False))
    op.create_index('ix_runtime_confirmations_line_id','runtime_confirmations',['line_id'])


def downgrade():
    raise RuntimeError('Measurement history is retained. Restore a reviewed backup for rollback.')
