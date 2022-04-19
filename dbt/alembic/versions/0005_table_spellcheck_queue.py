"""table_spellcheck_queue

Revision ID: 0005
Revises: 0004
Create Date: 1970-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        create table if not exists staging.spellcheck_queue (
              resource_id    uuid
            , resource_field resource_field
            , resource_type  resource_type   not null 
            , text_content   text            not null
            , derived_at     timestamp       not null

            , primary key (resource_id, resource_field)
        )
        """
    )


def downgrade():
    op.execute(
        """
        drop table if exists staging.spellcheck_queue cascade;
        """
    )
