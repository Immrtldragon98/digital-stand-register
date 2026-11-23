"""Track measured spare life and distinguish unknown stock from zero."""
import json
from alembic import op
import sqlalchemy as sa

revision = '20261123_spare_life'
down_revision = '20261123_pending_stands'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('inventory_items') as batch:
        batch.alter_column('quantity', existing_type=sa.Integer(), nullable=True, server_default=None)
    with op.batch_alter_table('inventory_transactions') as batch:
        batch.alter_column('quantity_before', existing_type=sa.Integer(), nullable=True)
    op.create_table('spare_life_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('inventory_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('life_hours', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('recorded_by', sa.String(150), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('life_hours > 0', name='ck_spare_life_positive'),
        sa.CheckConstraint('quantity > 0', name='ck_spare_life_quantity_positive'))
    op.create_index('ix_spare_life_records_item_id', 'spare_life_records', ['item_id'])
    # Populate the register's catalog only. Receipts do not establish stock or life.
    db = op.get_bind()
    latest = db.execute(sa.text("SELECT details FROM activity_logs WHERE action='SPARE_WORKBOOK_IMPORT' ORDER BY timestamp DESC, id DESC LIMIT 1")).scalar()
    if latest:
        report = json.loads(latest)
        names = {row['name'].strip() for plan in report.get('plans', []) for row in plan.get('rows', [])}
        names.update(row['name'].strip() for row in report.get('usage_summary', []))
        for name in sorted(names):
            db.execute(sa.text("""INSERT INTO inventory_items
                (name, quantity, minimum_quantity, location, criticality, is_active)
                VALUES (:name, NULL, 0, 'Store', 'UNASSESSED', true)
                ON CONFLICT (name) DO NOTHING"""), {'name': name})


def downgrade():
    # Life evidence and unknown stock cannot be losslessly downgraded.
    raise RuntimeError('Restore a database backup to downgrade without discarding spare-life evidence.')
