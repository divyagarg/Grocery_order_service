"""empty message

Revision ID: 6722ba460a4a
Revises: 1c1f460b722f
Create Date: 2016-05-26 15:39:40.164101

"""

# revision identifiers, used by Alembic.
revision = '6722ba460a4a'
down_revision = '1c1f460b722f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'cart_item', 'cart', ['cart_id'], ['cart_reference_uuid'])
    op.create_foreign_key(None, 'order_item', 'order', ['order_id'], ['order_reference_id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'order_item', type_='foreignkey')
    op.drop_constraint(None, 'cart_item', type_='foreignkey')
    ### end Alembic commands ###