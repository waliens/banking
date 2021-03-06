"""empty message

Revision ID: d8564e38689c
Revises: 
Create Date: 2022-05-27 08:39:40.658927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8564e38689c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rewrite_group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_group', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id_group'], ['group.id'], ),
    sa.PrimaryKeyConstraint('id', 'id_group')
    )
    op.create_table('rewrite_group_transaction',
    sa.Column('id_rewrite_group', sa.Integer(), nullable=False),
    sa.Column('id_transaction', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id_rewrite_group'], ['group.id'], ),
    sa.ForeignKeyConstraint(['id_transaction'], ['group.id'], ),
    sa.PrimaryKeyConstraint('id_rewrite_group', 'id_transaction')
    )
    op.add_column('transaction', sa.Column('is_rewrite', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transaction', 'is_rewrite')
    op.drop_table('rewrite_group_transaction')
    op.drop_table('rewrite_group')
    # ### end Alembic commands ###
