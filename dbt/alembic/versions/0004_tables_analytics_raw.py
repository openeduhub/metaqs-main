"""tables_analytics_raw

Revision ID: 0004
Revises: 0003
Create Date: 1970-01-01 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

schema = "raw"


def upgrade():
    op.create_table(
        "collections",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("doc", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("derived_at", postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("doc", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("derived_at", postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    op.execute(
        f"""
        create table {schema}.collections_previous_run
            as table {schema}.collections;
        create table {schema}.materials_previous_run
            as table {schema}.materials;
        """
    )


def downgrade():
    op.execute(
        f"""
        drop table if exists {schema}.materials_previous_run cascade;
        drop table if exists {schema}.collections_previous_run cascade;
        drop table if exists {schema}.materials cascade;
        drop table if exists {schema}.collections cascade;
        """
    )
