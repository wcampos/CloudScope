"""Initial schema

Revision ID: 000
Revises: None
Create Date: 2024-03-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '000'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create aws_profiles table
    op.create_table(
        'aws_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('aws_access_key_id', sa.String(100), nullable=False),
        sa.Column('aws_secret_access_key', sa.String(100), nullable=False),
        sa.Column('aws_session_token', sa.Text(), nullable=True),
        sa.Column('aws_region', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create schema_versions table
    op.create_table(
        'schema_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Drop tables in reverse order
    op.drop_table('schema_versions')
    op.drop_table('aws_profiles') 