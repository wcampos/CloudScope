"""Add custom_name and account_number columns

Revision ID: 001
Revises: 000
Create Date: 2024-03-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '001'
down_revision = '000'
branch_labels = None
depends_on = None


def _has_column(bind, table, column):
    return any(c['name'] == column for c in inspect(bind).get_columns(table))


def upgrade():
    bind = op.get_bind()
    if not _has_column(bind, 'aws_profiles', 'custom_name'):
        op.add_column('aws_profiles', sa.Column('custom_name', sa.String(100), nullable=True))
    if not _has_column(bind, 'aws_profiles', 'account_number'):
        op.add_column('aws_profiles', sa.Column('account_number', sa.String(12), nullable=True))


def downgrade():
    op.execute('ALTER TABLE aws_profiles DROP COLUMN IF EXISTS custom_name')
    op.execute('ALTER TABLE aws_profiles DROP COLUMN IF EXISTS account_number') 