"""Add timestamp columns

Revision ID: 003
Revises: 002
Create Date: 2024-03-18
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def _has_column(bind, table, column):
    return any(c["name"] == column for c in inspect(bind).get_columns(table))


def upgrade():
    bind = op.get_bind()
    if not _has_column(bind, "aws_profiles", "created_at"):
        op.add_column("aws_profiles", sa.Column("created_at", sa.DateTime(), nullable=True))
        op.execute("UPDATE aws_profiles SET created_at = NOW() WHERE created_at IS NULL")
        op.alter_column("aws_profiles", "created_at", nullable=False)
    if not _has_column(bind, "aws_profiles", "updated_at"):
        op.add_column("aws_profiles", sa.Column("updated_at", sa.DateTime(), nullable=True))
        op.execute("UPDATE aws_profiles SET updated_at = NOW() WHERE updated_at IS NULL")
        op.alter_column("aws_profiles", "updated_at", nullable=False)


def downgrade():
    op.execute("ALTER TABLE aws_profiles DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE aws_profiles DROP COLUMN IF EXISTS created_at")
