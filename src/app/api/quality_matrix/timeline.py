import os
from typing import Mapping

from databases import Database
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.quality_matrix.models import Base, QualityMatrix


def database_url():
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv(
        "POSTGRES_PORT", 5432
    )  # default postgres port is 5432
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


def engine():
    return create_engine(database_url())


def session():
    _engine = engine()
    Base.metadata.create_all(bind=_engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_timestamp(entry: QualityMatrix) -> int:
    return entry.timestamp


def timestamp_of_db_entry(entries: list[Mapping]):
    return list(map(get_timestamp, entries))


async def timestamps(database: Database):
    s = select([QualityMatrix])
    await database.connect()
    result: list[Mapping] = await database.fetch_all(s)

    if result is None:
        return []
    return timestamp_of_db_entry(result)
