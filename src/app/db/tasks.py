from databases import Database
from fastapi import FastAPI

from app.core.logging import logger
from app.db.core import create_timeline_table, database_url, has_table


async def connect_to_db(app: FastAPI) -> None:
    database = Database(database_url(), min_size=2, max_size=10)

    try:
        await database.connect()
        app.state._db = database
    except Exception as e:
        logger.warning(e)

    if not await has_table("timeline"):
        await create_timeline_table()


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.warning(e)
