"""Add force_password_change column to users table

Revision ID: 006_add_force_password_change_to_users
Revises: 005_create_password_reset_tokens
Create Date: 2024-01-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_force_password_change_to_users'
down_revision = '005_create_password_reset_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add force_password_change column to users table
    op.add_column(
        'users',
        sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    # Remove force_password_change column from users table
    op.drop_column('users', 'force_password_change')
