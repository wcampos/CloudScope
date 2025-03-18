"""Add missing columns

Revision ID: 002
Revises: 001
Create Date: 2024-03-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Add custom_name and account_number columns if they don't exist
    op.execute("""
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE aws_profiles ADD COLUMN custom_name VARCHAR(100);
            EXCEPTION
                WHEN duplicate_column THEN
                    NULL;
            END;
            
            BEGIN
                ALTER TABLE aws_profiles ADD COLUMN account_number VARCHAR(12);
            EXCEPTION
                WHEN duplicate_column THEN
                    NULL;
            END;
        END $$;
    """)

def downgrade():
    # Remove the columns if they exist
    op.execute("""
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE aws_profiles DROP COLUMN IF EXISTS custom_name;
            EXCEPTION
                WHEN undefined_column THEN
                    NULL;
            END;
            
            BEGIN
                ALTER TABLE aws_profiles DROP COLUMN IF EXISTS account_number;
            EXCEPTION
                WHEN undefined_column THEN
                    NULL;
            END;
        END $$;
    """) 