"""Add custom_name and account_number columns

Revision ID: 001
Revises: 000
Create Date: 2024-03-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = '000'
branch_labels = None
depends_on = None

def upgrade():
    # Add custom_name and account_number columns
    op.add_column('aws_profiles', sa.Column('custom_name', sa.String(100), nullable=True))
    op.add_column('aws_profiles', sa.Column('account_number', sa.String(12), nullable=True))

def downgrade():
    # Remove the columns
    op.drop_column('aws_profiles', 'custom_name')
    op.drop_column('aws_profiles', 'account_number') 