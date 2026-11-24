"""Individual component life identities and atomic preparation stock mapping."""
from alembic import op
import sqlalchemy as sa
revision = '20261124_component_lifecycle'
down_revision = '20261124_line_runtime'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stand_component_types', sa.Column('inventory_item_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_component_type_inventory', 'stand_component_types', 'inventory_items', ['inventory_item_id'], ['id'])
    op.create_table('component_assets', sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('code',sa.String(100),unique=True,nullable=False),
        sa.Column('component_type_id',sa.Integer(),sa.ForeignKey('stand_component_types.id'),nullable=False),
        sa.Column('condition',sa.String(12),nullable=False),sa.Column('prior_life_hours',sa.Float(),nullable=True),
        sa.Column('created_at',sa.DateTime(),nullable=False))
    op.create_index('ix_component_assets_component_type_id','component_assets',['component_type_id'])
    op.create_table('component_fittings',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('asset_id',sa.Integer(),sa.ForeignKey('component_assets.id'),nullable=False),
        sa.Column('stand_id',sa.Integer(),sa.ForeignKey('stand_assets.id'),nullable=False),
        sa.Column('preparation_id',sa.Integer(),sa.ForeignKey('stand_component_preparations.id'),nullable=False),
        sa.Column('fitted_at',sa.DateTime(),nullable=False),sa.Column('removed_at',sa.DateTime(),nullable=True))
    op.create_index('ix_component_fittings_asset_id','component_fittings',['asset_id'])
    op.create_index('ix_component_fittings_stand_id','component_fittings',['stand_id'])
    op.create_index('uq_active_component_fitting','component_fittings',['asset_id'],unique=True,postgresql_where=sa.text('removed_at IS NULL'))
    op.create_table('preparation_asset_selections',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('preparation_id',sa.Integer(),sa.ForeignKey('stand_component_preparations.id',ondelete='CASCADE'),nullable=False),
        sa.Column('component_type_id',sa.Integer(),sa.ForeignKey('stand_component_types.id'),nullable=False),
        sa.Column('asset_id',sa.Integer(),sa.ForeignKey('component_assets.id'),nullable=False),
        sa.UniqueConstraint('preparation_id','asset_id',name='uq_preparation_component_asset'))
    op.create_index('ix_preparation_asset_selections_preparation_id','preparation_asset_selections',['preparation_id'])


def downgrade():
    raise RuntimeError('Component identity and consumption evidence cannot be discarded by downgrade.')
