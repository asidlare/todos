"""limits db schema

Revision ID: d472490748ab
Revises: 535906879d1f
Create Date: 2019-08-19 18:06:07.109556

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd472490748ab'
down_revision = '535906879d1f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('TaskCount',
                    sa.Column('todolist_id', sa.CHAR(length=36), nullable=False),
                    sa.Column('quantity', mysql.SMALLINT(unsigned=True), nullable=False),
                    sa.ForeignKeyConstraint(['todolist_id'], ['TodoList.todolist_id'],
                                            name=op.f('fk_TaskCount_todolist_id_TodoList'), ondelete='cascade'),
                    sa.PrimaryKeyConstraint('todolist_id', name=op.f('pk_TaskCount'))
                    )
    op.create_table('TaskDepth',
                    sa.Column('task_id', sa.CHAR(length=36), nullable=False),
                    sa.Column('depth', mysql.SMALLINT(unsigned=True), nullable=False),
                    sa.ForeignKeyConstraint(['task_id'], ['Task.task_id'], name=op.f('fk_TaskDepth_task_id_Task'),
                                            ondelete='cascade'),
                    sa.PrimaryKeyConstraint('task_id', name=op.f('pk_TaskDepth'))
                    )
    op.add_column('Role', sa.Column('task_count_limit', mysql.SMALLINT(unsigned=True), nullable=True))
    op.add_column('Role', sa.Column('task_depth_limit', mysql.SMALLINT(unsigned=True), nullable=True))
    op.add_column('Role', sa.Column('todolist_count_limit', mysql.SMALLINT(unsigned=True), nullable=True))

    bind = op.get_bind()
    # metadata for current connection
    meta = sa.MetaData(bind=bind)
    # tuple with tables to reflect
    meta.reflect()

    # update limits
    op.execute('UPDATE Role SET todolist_count_limit = 10, task_count_limit = 100, '
               'task_depth_limit = 10 WHERE role = "owner"')
    op.execute('UPDATE Role SET task_count_limit = 80, task_depth_limit = 8 WHERE role = "admin"')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Role', 'todolist_count_limit')
    op.drop_column('Role', 'task_depth_limit')
    op.drop_column('Role', 'task_count_limit')
    op.drop_table('TaskDepth')
    op.drop_table('TaskCount')
    # ### end Alembic commands ###
