import json
from functools import lru_cache
from pprint import pformat
from typing import Iterator, Tuple

import asyncpg
from asyncpg.pool import Pool
from fastapi_utils.session import FastAPISessionMaker
from sqlalchemy.dialects.postgresql import pypostgresql
from sqlalchemy.orm import Session
from sqlalchemy.sql import ClauseElement

from app.core.config import DATABASE_URL, MAX_CONNECTIONS_COUNT, MIN_CONNECTIONS_COUNT
from app.core.logging import logger

dialect = pypostgresql.dialect(paramstyle="pyformat")
dialect.implicit_returning = True
dialect.supports_native_enum = True
dialect.supports_smallserial = True
dialect._backslash_escapes = False
dialect.supports_sane_multi_rowcount = True
dialect._has_native_hstore = True


def get_postgres() -> Iterator[Session]:
    """FastAPI dependency that provides a sqlalchemy session"""
    yield from _get_fastapi_sessionmaker().get_db()


@lru_cache()
def _get_fastapi_sessionmaker() -> FastAPISessionMaker:
    return FastAPISessionMaker(str(DATABASE_URL))


class AsyncPg:
    pool: Pool = None


_async_Pg = AsyncPg()


async def get_postgres_async() -> Pool:
    """FastAPI dependency that provides a asyncpg connection"""
    if not _async_Pg.pool:
        await connect_to_postgres()
    return _async_Pg.pool


async def connect_to_postgres():
    async def init(conn: asyncpg.Connection):
        await conn.set_type_codec(
            "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )

    _async_Pg.pool = await asyncpg.create_pool(
        str(DATABASE_URL),
        min_size=MIN_CONNECTIONS_COUNT,
        max_size=MAX_CONNECTIONS_COUNT,
        init=init,
        server_settings={"search_path": "analytics, public"},
    )


async def close_postgres_connection():
    if _async_Pg.pool:
        await _async_Pg.pool.close()


# TODO: Unused
def compile_query(query: ClauseElement) -> Tuple[str, list, tuple]:
    compiled = query.compile(dialect=dialect)
    compiled_params = sorted(compiled.params.items())

    mapping = {key: "$" + str(i) for i, (key, _) in enumerate(compiled_params, start=1)}
    compiled_query = compiled.string % mapping

    processors = compiled._bind_processors
    params = [
        processors[key](val) if key in processors else val
        for key, val in compiled_params
    ]

    logger.debug(
        f"Compiled query to postgres:\n{pformat(compiled_query)}\nParams:\n{pformat(params)}"
    )

    return compiled_query, params, compiled._result_columns
