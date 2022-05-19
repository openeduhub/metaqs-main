from databases import Database
from fastapi import FastAPI

from app.core.logging import logger
from app.db.core import database_url


async def connect_to_db(app: FastAPI) -> None:
    database = Database(database_url(), min_size=2, max_size=10)

    try:
        await database.connect()
        app.state._db = database
    except Exception as e:
        logger.warning(e)


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.warning(e)
