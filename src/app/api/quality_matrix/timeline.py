import os
from typing import Mapping

from databases import Database
from sqlalchemy import (
    JSON,
    Column,
    Integer,
    MetaData,
    Table,
    create_engine,
    inspect,
    select,
)

from app.api.quality_matrix.models import Timeline


def database_url():
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv(
        "POSTGRES_PORT", 5432
    )  # default postgres port is 5432
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


def get_timestamp(entry: Timeline) -> int:
    return entry.timestamp


def timestamp_of_db_entry(entries: list[Mapping]):
    return list(map(get_timestamp, entries))


async def timestamps(database: Database):
    if not await has_table("timeline"):
        await create_timeline_table()

    s = select([Timeline])
    await database.connect()
    result: list[Mapping] = await database.fetch_all(s)

    if result is None:
        return []
    return timestamp_of_db_entry(result)


async def has_table(name: str):
    engine = create_engine(database_url())
    ins = inspect(engine)
    return ins.dialect.has_table(engine.connect(), name)


async def create_timeline_table():
    engine = create_engine(database_url())
    meta = MetaData(engine)
    timeline_table = Table(
        "timeline",
        meta,
        Column("id", Integer),
        Column("timestamp", Integer),
        Column("quality_matrix", JSON),
    )
    with engine.connect():
        timeline_table.create()
