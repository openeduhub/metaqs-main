"""custom_functions

Revision ID: 0003
Revises: 0002
Create Date: 1970-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        """
        create or replace function txt2ltxt(_txt text)
            returns text
            language sql as
        $$
        select replace(_txt, '-', '_')
        $$;


        create or replace function ltxt2txt(_ltxt text)
            returns text
            language sql as
        $$
        select replace(_ltxt, '_', '-')
        $$;


        create or replace function uuid2ltree(_uuid uuid)
            returns ltree
            language sql as
        $$
        select replace(_uuid::text, '-', '_')::ltree
        $$;


        create or replace function ltree2uuid(_ltree ltree)
            returns uuid
            language sql as
        $$
        select replace(ltree2text(_ltree), '_', '-')::uuid
        $$;


        create or replace function ltree2uuids(_path ltree)
            returns uuid[]
            language sql as
        $$
        select string_to_array(replace(ltree2text(_path), '_', '-'), '.')::uuid[]
        $$;


        create or replace function empty_str2null(_value text)
            returns text
            language sql as
        $$
        select nullif(
            regexp_replace(
                regexp_replace(
                    _value,
                    '[\s\n]*$',
                    ''
                ),
                '^[\s\n]*',
                ''
            ),
            ''
        )
        $$;


        create or replace function empty_str2sentinel(_value text, _sentinel text)
            returns text
            language sql as
        $$
        select regexp_replace(
                       _value,
                       '^[\s\n]*$',
                       _sentinel
                   );
        $$;


        create or replace function empty_jsonb_array2null(_value jsonb)
            returns jsonb
            language sql as
        $$
        select nullif(_value, '[""]'::jsonb)
        $$;


        create or replace function shorten_vocab(_value text, _vocab_type text)
            returns text
            language sql as
        $$
        select regexp_replace(
                       _value,
                       '^https?://w3id.org/openeduhub/vocabs/' || _vocab_type || '/',
                       ''
                   );
        $$;


        create or replace function null2jsonb_array(_value jsonb)
            returns jsonb
            language sql as
        $$
        select coalesce(_value, ('[' || '"fehlend"' || ']')::jsonb);
        $$;
        """
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        """
        drop function if exists null2jsonb_array cascade;
        drop function if exists shorten_vocab cascade;
        drop function if exists empty_jsonb_array2null cascade;
        drop function if exists empty_str2sentinel cascade;
        drop function if exists empty_str2null cascade;
        drop function if exists ltree2uuids cascade;
        drop function if exists ltree2uuid cascade;
        drop function if exists uuid2ltree cascade;
        drop function if exists ltxt2txt cascade;
        drop function if exists txt2ltxt cascade;
        """
    )
