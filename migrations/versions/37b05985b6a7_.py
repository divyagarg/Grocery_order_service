"""empty message

Revision ID: 37b05985b6a7
Revises: 5fd0f1e7f09c
Create Date: 2016-05-17 12:25:28.172312

"""

# revision identifiers, used by Alembic.
revision = '37b05985b6a7'
down_revision = '5fd0f1e7f09c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cart__item', sa.Column('transferPrice', sa.Float(precision='10,2'), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cart__item', 'transferPrice')
    ### end Alembic commands ###
