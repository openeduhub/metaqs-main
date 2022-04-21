"""table_search_stats

Revision ID: 0007
Revises: 0006
Create Date: 1970-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        create table if not exists store.search_stats (
              resource_id    uuid
            , resource_field text
            , resource_type  text       not null
            , searchtext     text       not null
            , derived_at     timestamp  not null
            , stats          jsonb      not null

            , primary key (resource_id, resource_field)
        )
        """
    )


def downgrade():
    op.execute(
        """
        drop table if exists store.search_stats cascade;
        """
    )
