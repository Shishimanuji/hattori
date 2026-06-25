"""Create password reset tokens table

Revision ID: 005_create_password_reset_tokens
Revises: 004_create_sessions_table
Create Date: 2024-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_create_password_reset_tokens'
down_revision = '004_create_sessions_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('temporary_password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_password_reset_tokens_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_user_id', table_name='password_reset_tokens')
    
    # Drop table
    op.drop_table('password_reset_tokens')
