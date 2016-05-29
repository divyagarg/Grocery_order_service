"""empty message

Revision ID: 3d2e810dc66b
Revises: 5a966f1269e9
Create Date: 2016-05-26 20:49:07.654251

"""

# revision identifiers, used by Alembic.
revision = '3d2e810dc66b'
down_revision = '5a966f1269e9'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('address', 'pincode',
               existing_type=mysql.VARCHAR(length=512),
               nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('address', 'pincode',
               existing_type=mysql.VARCHAR(length=512),
               nullable=False)
    ### end Alembic commands ###