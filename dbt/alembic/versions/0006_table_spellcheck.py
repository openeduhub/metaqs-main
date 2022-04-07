"""table_spellcheck

Revision ID: 0006
Revises: 0005
Create Date: 1970-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        create table if not exists store.spellcheck (
              resource_id    uuid
            , resource_field text
            , resource_type  text       not null 
            , text_content   text       not null
            , derived_at     timestamp  not null
            , error          jsonb      not null
            
            , primary key (resource_id, resource_field)
        )
        """
    )


def downgrade():
    pass
    # uncomment if you do not care about store.spellcheck table
    # op.execute(
    #     """
    #     drop table if exists store.spellcheck cascade;
    #     """
    # )
