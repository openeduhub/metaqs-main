"""init

Revision ID: 0001
Revises: 
Create Date: 1970-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        """
        create extension if not exists ltree;
        create schema if not exists raw;
        create schema if not exists staging;
        create schema if not exists store;
        """
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        """
        -- drop schema if exists store cascade;
        drop schema if exists staging cascade;
        drop schema if exists raw cascade;
        drop extension if exists ltree;
        """
    )
