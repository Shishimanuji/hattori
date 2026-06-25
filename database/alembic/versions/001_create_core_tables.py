"""Create core database tables

Revision ID: 001_create_core_tables
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_core_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create custom ENUM types
    user_role_enum = postgresql.ENUM('Admin', 'Manager', 'Analyst', 'Viewer', name='user_role')
    project_status_enum = postgresql.ENUM('Active', 'Pending', 'Completed', 'On Hold', name='project_status')
    resource_status_enum = postgresql.ENUM('Active', 'Inactive', 'Archived', name='resource_status')
    custom_field_type_enum = postgresql.ENUM('text', 'number', 'date', 'dropdown', 'boolean', name='custom_field_type')
    
    user_role_enum.create(op.get_bind(), checkfirst=True)
    project_status_enum.create(op.get_bind(), checkfirst=True)
    resource_status_enum.create(op.get_bind(), checkfirst=True)
    custom_field_type_enum.create(op.get_bind(), checkfirst=True)
    
    # ============================================================================
    # Create USERS table
    # ============================================================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False, server_default='Viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_deleted_at', 'users', ['deleted_at'])
    
    # ============================================================================
    # Create PROJECTS table
    # ============================================================================
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', project_status_enum, nullable=False, server_default='Active'),
        sa.Column('budget', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('allocated_budget', sa.DECIMAL(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_deleted_at', 'projects', ['deleted_at'])
    op.create_index('idx_projects_created_at', 'projects', ['created_at'])
    
    # ============================================================================
    # Create ASSET_TYPES table
    # ============================================================================
    op.create_table(
        'asset_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_asset_types_is_active', 'asset_types', ['is_active'])
    op.create_index('idx_asset_types_name', 'asset_types', ['name'])
    
    # ============================================================================
    # Create CUSTOM_FIELDS table
    # ============================================================================
    op.create_table(
        'custom_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('asset_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(255), nullable=False),
        sa.Column('field_type', custom_field_type_enum, nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('options', postgresql.JSON(none_as_null=True), nullable=True),
        sa.Column('validation_rules', postgresql.JSON(none_as_null=True), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['asset_type_id'], ['asset_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_type_id', 'field_name', name='uq_asset_type_field_name')
    )
    op.create_index('idx_custom_fields_asset_type_id', 'custom_fields', ['asset_type_id'])
    op.create_index('idx_custom_fields_field_type', 'custom_fields', ['field_type'])
    
    # ============================================================================
    # Create RESOURCES table
    # ============================================================================
    op.create_table(
        'resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cost', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('status', resource_status_enum, nullable=False, server_default='Active'),
        sa.Column('allocation_date', sa.Date(), nullable=False),
        sa.Column('custom_field_values', postgresql.JSON(none_as_null=True), nullable=False, server_default='{}'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['asset_type_id'], ['asset_types.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_resources_project_id', 'resources', ['project_id'])
    op.create_index('idx_resources_asset_type_id', 'resources', ['asset_type_id'])
    op.create_index('idx_resources_status', 'resources', ['status'])
    op.create_index('idx_resources_deleted_at', 'resources', ['deleted_at'])
    op.create_index('idx_resources_allocation_date', 'resources', ['allocation_date'])
    op.create_index('idx_resources_created_by', 'resources', ['created_by'])
    op.create_index('idx_resources_created_at', 'resources', ['created_at'])
    
    # Create GIN index for JSONB queries
    op.execute("""
        CREATE INDEX idx_resources_custom_fields_gin 
        ON resources USING GIN(custom_field_values)
    """)


def downgrade() -> None:
    # Drop resources table and indexes
    op.drop_index('idx_resources_custom_fields_gin', table_name='resources')
    op.drop_index('idx_resources_created_at', table_name='resources')
    op.drop_index('idx_resources_created_by', table_name='resources')
    op.drop_index('idx_resources_allocation_date', table_name='resources')
    op.drop_index('idx_resources_deleted_at', table_name='resources')
    op.drop_index('idx_resources_status', table_name='resources')
    op.drop_index('idx_resources_asset_type_id', table_name='resources')
    op.drop_index('idx_resources_project_id', table_name='resources')
    op.drop_table('resources')
    
    # Drop custom_fields table and indexes
    op.drop_index('idx_custom_fields_field_type', table_name='custom_fields')
    op.drop_index('idx_custom_fields_asset_type_id', table_name='custom_fields')
    op.drop_table('custom_fields')
    
    # Drop asset_types table and indexes
    op.drop_index('idx_asset_types_name', table_name='asset_types')
    op.drop_index('idx_asset_types_is_active', table_name='asset_types')
    op.drop_table('asset_types')
    
    # Drop projects table and indexes
    op.drop_index('idx_projects_created_at', table_name='projects')
    op.drop_index('idx_projects_deleted_at', table_name='projects')
    op.drop_index('idx_projects_status', table_name='projects')
    op.drop_index('idx_projects_owner_id', table_name='projects')
    op.drop_table('projects')
    
    # Drop users table and indexes
    op.drop_index('idx_users_deleted_at', table_name='users')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS custom_field_type')
    op.execute('DROP TYPE IF EXISTS resource_status')
    op.execute('DROP TYPE IF EXISTS project_status')
    op.execute('DROP TYPE IF EXISTS user_role')
