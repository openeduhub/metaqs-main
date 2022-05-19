import os
from urllib.parse import quote

from sqlalchemy import MetaData, create_engine, inspect

from app.api.quality_matrix.models import timeline_table


def database_url():
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = quote(os.getenv("POSTGRES_PASSWORD"))
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv(
        "POSTGRES_PORT", 5432
    )  # default postgres port is 5432
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


async def has_table(name: str):
    engine = create_engine(database_url())
    ins = inspect(engine)
    return ins.dialect.has_table(engine.connect(), name)


async def get_table():
    engine = create_engine(database_url())
    meta = MetaData(engine)
    table = timeline_table(meta)
    return engine, table


async def create_timeline_table():
    engine, table = await get_table()
    with engine.connect():
        table.create()
