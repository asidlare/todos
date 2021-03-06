"""initial migration with User table

Revision ID: 918218055057
Revises: 
Create Date: 2019-08-07 12:32:07.359798

""" # noqa
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '918218055057'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('User',
                    sa.Column('user_id', sa.CHAR(length=36), nullable=False),
                    sa.Column('login', sa.String(length=80), nullable=False),
                    sa.Column('password', sqlalchemy_utils.types.password.PasswordType(max_length=1137), nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('email', sqlalchemy_utils.types.email.EmailType(length=255), nullable=False),
                    sa.Column('created', mysql.DATETIME(), nullable=False),
                    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_User')),
                    sa.UniqueConstraint('email', name=op.f('uq_User_email')),
                    sa.UniqueConstraint('login', name=op.f('uq_User_login'))
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('User')
    # ### end Alembic commands ###
