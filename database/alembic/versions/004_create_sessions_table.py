"""Create sessions table for authentication

Revision ID: 004_create_sessions_table
Revises: 003_create_relationships_and_foreign_keys
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_create_sessions_table'
down_revision = '003_create_relationships_and_foreign_keys'
branch_labels = None
depends_on = None

# Ensure proper revision chaining: 001 -> 003 -> 004


def upgrade() -> None:
    """
    Create sessions table for authentication token management.
    
    Purpose:
    - Track active authentication sessions
    - Store JWT token hashes (not full tokens for security)
    - Enable session invalidation (logout)
    - Track session expiration for auto-cleanup
    - Support session timeout warnings and auto-logout
    
    Configuration:
    - token_hash should be SHA256 hash of JWT token (not the token itself)
    - expires_at = created_at + 24 hours (configurable)
    - last_activity updated on each API request
    - Idle timeout: 30 minutes, auto-logout after 35 minutes
    - Multiple sessions per user supported (e.g., login on different devices)
    """
    
    # ============================================================================
    # Create SESSIONS table
    # ============================================================================
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('invalidated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ============================================================================
    # Create indexes for query optimization
    # ============================================================================
    
    # Index for finding active sessions by user (common query: find all sessions for a user)
    op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
    
    # Index for token validation (fast token lookup during authentication)
    op.create_index('idx_sessions_token_hash', 'sessions', ['token_hash'])
    
    # Index for cleanup of expired sessions (query by expiration time for batch cleanup)
    op.create_index('idx_sessions_expires_at', 'sessions', ['expires_at'])
    
    # Index for idle timeout detection (query by last_activity to find idle sessions)
    op.create_index('idx_sessions_last_activity', 'sessions', ['last_activity'])
    
    # Index for active session filtering (filter by is_active status in queries)
    op.create_index('idx_sessions_is_active', 'sessions', ['is_active'])
    
    # Composite index for common session lookup query: find active session by user and token
    op.create_index('idx_sessions_user_active_token', 'sessions', ['user_id', 'is_active', 'token_hash'])
    
    # Composite index for cleanup queries: find expired active sessions
    op.create_index('idx_sessions_cleanup', 'sessions', ['is_active', 'expires_at'])


def downgrade() -> None:
    # Drop all indexes
    op.drop_index('idx_sessions_cleanup', table_name='sessions')
    op.drop_index('idx_sessions_user_active_token', table_name='sessions')
    op.drop_index('idx_sessions_is_active', table_name='sessions')
    op.drop_index('idx_sessions_last_activity', table_name='sessions')
    op.drop_index('idx_sessions_expires_at', table_name='sessions')
    op.drop_index('idx_sessions_token_hash', table_name='sessions')
    op.drop_index('idx_sessions_user_id', table_name='sessions')
    
    # Drop table
    op.drop_table('sessions')
