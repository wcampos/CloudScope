"""Initial schema

Revision ID: 000
Revises: None
Create Date: 2024-03-18
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "000"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(bind, name):
    return inspect(bind).has_table(name)


def upgrade():
    bind = op.get_bind()
    # Create aws_profiles table only if it does not exist (idempotent; app may have run db.create_all() first)
    if not _table_exists(bind, "aws_profiles"):
        op.create_table(
            "aws_profiles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("aws_access_key_id", sa.String(100), nullable=False),
            sa.Column("aws_secret_access_key", sa.String(100), nullable=False),
            sa.Column("aws_session_token", sa.Text(), nullable=True),
            sa.Column("aws_region", sa.String(50), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.PrimaryKeyConstraint("id"),
        )

    # Create schema_versions table only if it does not exist
    if not _table_exists(bind, "schema_versions"):
        op.create_table(
            "schema_versions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("version", sa.String(50), nullable=False),
            sa.Column("applied_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade():
    op.execute("DROP TABLE IF EXISTS schema_versions")
    op.execute("DROP TABLE IF EXISTS aws_profiles")
