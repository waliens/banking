"""empty message

Revision ID: 5a30197c7053
Revises: 
Create Date: 2023-12-16 13:11:21.160160

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from db.database import add_tags, add_default_user, add_currencies


# revision identifiers, used by Alembic.
revision = '5a30197c7053'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('id_parent', sa.Integer(), nullable=True),
    sa.Column('color', sa.String(length=255), nullable=True),
    sa.Column('icon', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id_parent'], ['category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('currency',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sa.String(length=15), nullable=True),
    sa.Column('short_name', sa.String(length=255), nullable=True),
    sa.Column('long_name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('description', sa.String(length=1024), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ml_model_file',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(), nullable=True),
    sa.Column('target', sa.String(), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('state', sa.Enum('INVALID', 'VALID', 'TRAINING', 'DELETED', name='mlmodelstate'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('account',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number', sa.String(length=63), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('initial', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('id_currency', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id_currency'], ['currency.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('number', 'name', name='account_name_number_unique_constraint')
    )
    op.create_table('account_alias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number', sa.String(length=63), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('id_account', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id_account'], ['account.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('account_group',
    sa.Column('id_group', sa.Integer(), nullable=False),
    sa.Column('id_account', sa.Integer(), nullable=False),
    sa.Column('contribution_ratio', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['id_account'], ['account.id'], ),
    sa.ForeignKeyConstraint(['id_group'], ['group.id'], ),
    sa.PrimaryKeyConstraint('id_group', 'id_account')
    )
    op.create_table('transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('custom_id', sa.String(length=255), nullable=True),
    sa.Column('id_source', sa.Integer(), nullable=True),
    sa.Column('id_dest', sa.Integer(), nullable=True),
    sa.Column('when', sa.Date(), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('id_currency', sa.Integer(), nullable=True),
    sa.Column('id_category', sa.Integer(), nullable=True),
    sa.Column('data_source', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id_category'], ['category.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['id_currency'], ['currency.id'], ),
    sa.ForeignKeyConstraint(['id_dest'], ['account.id'], ),
    sa.ForeignKeyConstraint(['id_source'], ['account.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('custom_id')
    )
    op.create_table('transaction_group',
    sa.Column('id_group', sa.Integer(), nullable=False),
    sa.Column('id_transaction', sa.Integer(), nullable=False),
    sa.Column('contribution_ratio', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['id_group'], ['group.id'], ),
    sa.ForeignKeyConstraint(['id_transaction'], ['transaction.id'], ),
    sa.PrimaryKeyConstraint('id_group', 'id_transaction')
    )

    bind = op.get_bind()
    session = orm.Session(bind=bind)
    add_tags(sess=session)
    add_currencies(sess=session)
    add_default_user(sess=session)
    session.commit()
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transaction_group')
    op.drop_table('transaction')
    op.drop_table('account_group')
    op.drop_table('account_alias')
    op.drop_table('account')
    op.drop_table('user')
    op.drop_table('ml_model_file')
    op.drop_table('group')
    op.drop_table('currency')
    op.drop_table('category')
    # ### end Alembic commands ###
