"""create_event_table

Revision ID: 89fec1d69a9d
Revises: 133b4e91f81b
Create Date: 2019-04-23 10:18:50.019797

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '89fec1d69a9d'
down_revision = '133b4e91f81b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('event',
    sa.Column('id', postgresql.UUID(), nullable=False),
    sa.Column('user_id', postgresql.UUID(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user_account.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_started_at'), 'event', ['started_at'], unique=False)
    op.create_index(op.f('ix_event_user_id'), 'event', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_event_user_id'), table_name='event')
    op.drop_index(op.f('ix_event_started_at'), table_name='event')
    op.drop_table('event')
    # ### end Alembic commands ###