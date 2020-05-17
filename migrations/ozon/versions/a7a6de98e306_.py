"""empty message

Revision ID: a7a6de98e306
Revises: 92b82850b5c3
Create Date: 2020-05-14 21:31:02.523642

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a7a6de98e306'
down_revision = '92b82850b5c3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('brand_id', sa.Integer(), nullable=True))
    op.add_column('item', sa.Column('seller_id', sa.Integer(), nullable=True))
    op.drop_column('item', 'seller')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('seller', mysql.VARCHAR(collation='utf8_unicode_ci', length=100), nullable=True))
    op.drop_column('item', 'seller_id')
    op.drop_column('item', 'brand_id')
    # ### end Alembic commands ###
