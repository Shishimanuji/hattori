"""Create relationships and foreign keys (allocations and audit_logs tables)

Revision ID: 003_create_relationships_and_foreign_keys
Revises: 001_create_core_tables
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_relationships_and_foreign_keys'
down_revision = '001_create_core_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create allocations and audit_logs tables for budget tracking and change history.
    Note: Foreign key constraints are already created in migration 001_create_core_tables.py
    """
    
    # ============================================================================
    # 1. CREATE ALLOCATIONS TABLE (for budget tracking)
    # ============================================================================
    op.create_table(
        'allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cost_at_allocation', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('allocated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('deallocated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on allocations for query performance
    op.create_index('idx_allocations_resource_id', 'allocations', ['resource_id'])
    op.create_index('idx_allocations_project_id', 'allocations', ['project_id'])
    op.create_index('idx_allocations_allocated_at', 'allocations', ['allocated_at'])
    op.create_index('idx_allocations_deallocated_at', 'allocations', ['deallocated_at'])
    
    # ============================================================================
    # 2. CREATE AUDIT_LOGS TABLE (for change history and compliance)
    # ============================================================================
    
    # Create ENUM for audit operations
    audit_operation_enum = postgresql.ENUM(
        'CREATE', 'UPDATE', 'DELETE', 'IMPORT', 'EXPORT', 'LOGIN', 'LOGOUT',
        'ROLE_CHANGE', 'REPORT_DOWNLOAD', 'CONFIG_CHANGE',
        name='audit_operation'
    )
    audit_operation_enum.create(op.get_bind(), checkfirst=True)
    
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation', audit_operation_enum, nullable=False),
        sa.Column('old_values', postgresql.JSON(none_as_null=True), nullable=True),
        sa.Column('new_values', postgresql.JSON(none_as_null=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on audit_logs for query performance and compliance
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_operation', 'audit_logs', ['operation'])
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_status', 'audit_logs', ['status'])
    
    # ============================================================================
    # 3. CREATE COMPOSITE INDEXES FOR COMMON QUERIES
    # ============================================================================
    
    # Composite index for common resource filtering
    op.create_index('idx_resources_project_status', 'resources', ['project_id', 'status'])
    
    # Composite index for allocation queries
    op.create_index('idx_allocations_project_allocated', 'allocations', ['project_id', 'allocated_at'])
    
    # Composite index for audit log searches
    op.create_index('idx_audit_logs_entity_operation', 'audit_logs', ['entity_type', 'operation', 'created_at'])


def downgrade() -> None:
    # Drop composite indexes
    op.drop_index('idx_audit_logs_entity_operation', table_name='audit_logs')
    op.drop_index('idx_allocations_project_allocated', table_name='allocations')
    op.drop_index('idx_resources_project_status', table_name='resources')
    
    # Drop audit_logs indexes
    op.drop_index('idx_audit_logs_status', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity', table_name='audit_logs')
    op.drop_index('idx_audit_logs_operation', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    
    # Drop audit_logs table
    op.drop_table('audit_logs')
    
    # Drop ENUM type
    op.execute('DROP TYPE IF EXISTS audit_operation')
    
    # Drop allocations indexes
    op.drop_index('idx_allocations_deallocated_at', table_name='allocations')
    op.drop_index('idx_allocations_allocated_at', table_name='allocations')
    op.drop_index('idx_allocations_project_id', table_name='allocations')
    op.drop_index('idx_allocations_resource_id', table_name='allocations')
    
    # Drop allocations table
    op.drop_table('allocations')
