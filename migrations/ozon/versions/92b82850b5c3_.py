"""empty message

Revision ID: 92b82850b5c3
Revises: 2258727bf914
Create Date: 2020-05-14 17:54:02.111660

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92b82850b5c3'
down_revision = '2258727bf914'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('catalog', sa.Column('end_point', sa.BOOLEAN(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('catalog', 'end_point')
    # ### end Alembic commands ###