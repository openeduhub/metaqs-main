from databases import Database
from fastapi import FastAPI

from app.api.quality_matrix.timeline import database_url
from app.core.logging import logger


async def connect_to_db(app: FastAPI) -> None:
    database = Database(
        database_url(), min_size=2, max_size=10
    )  # these can be configured in config as well

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
