"""empty message

Revision ID: 1b3e057c011e
Revises: 237e8ed2fe79
Create Date: 2016-06-23 21:01:39.293232

"""

# revision identifiers, used by Alembic.
revision = '1b3e057c011e'
down_revision = '237e8ed2fe79'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('cart_geo_user_idx', table_name='cart')
    op.add_column('master_order', sa.Column('promo_max_discount', sa.Float(precision='10,2'), nullable=True))
    op.add_column('master_order', sa.Column('promo_types', sa.String(length=255), nullable=True))
    op.add_column('order', sa.Column('promo_max_discount', sa.Float(precision='10,2'), nullable=True))
    op.add_column('order', sa.Column('promo_types', sa.String(length=255), nullable=True))
    op.drop_index('order_user_idx', table_name='order')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index('order_user_idx', 'order', ['user_id'], unique=False)
    op.drop_column('order', 'promo_types')
    op.drop_column('order', 'promo_max_discount')
    op.drop_column('master_order', 'promo_types')
    op.drop_column('master_order', 'promo_max_discount')
    op.create_index('cart_geo_user_idx', 'cart', ['geo_id', 'user_id'], unique=False)
    ### end Alembic commands ###