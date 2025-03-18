"""Add timestamp columns

Revision ID: 003
Revises: 002
Create Date: 2024-03-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at and updated_at columns
    op.add_column('aws_profiles', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('aws_profiles', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Set default values for existing rows
    op.execute("UPDATE aws_profiles SET created_at = NOW(), updated_at = NOW()")

    # Make columns not nullable
    op.alter_column('aws_profiles', 'created_at', nullable=False)
    op.alter_column('aws_profiles', 'updated_at', nullable=False)

def downgrade():
    # Remove the columns
    op.drop_column('aws_profiles', 'updated_at')
    op.drop_column('aws_profiles', 'created_at') 