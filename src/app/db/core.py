import os
from urllib.parse import quote

from sqlalchemy import create_engine, inspect

from app.api.quality_matrix.models import Timeline


def database_url():
    postgres_user: str = os.getenv("POSTGRES_USER")
    postgres_password = quote(os.getenv("POSTGRES_PASSWORD"))
    postgres_server: str = os.getenv("POSTGRES_SERVER", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", 5432)
    postgres_db: str = os.getenv("POSTGRES_DB")
    return f"postgresql://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"


async def has_table(name: str):
    engine = create_engine(database_url())
    inspection = inspect(engine)
    return inspection.dialect.has_table(engine.connect(), name)


async def create_timeline_table():
    engine = create_engine(database_url())
    with engine.connect():
        Timeline.create()
