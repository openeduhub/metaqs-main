from databases import Database
from fastapi import FastAPI

from app.core.logging import logger
from app.db.core import database_url


async def connect_to_db(app: FastAPI) -> None:
    logger.info("Instantiating database")
    database = Database(database_url(), min_size=2, max_size=10)

    try:
        await database.connect()
        await database.execute(
            """
        create table if not exists timeline
        (
            id        int,
            timestamp int,
            mode      text,
            quality   json,
            total     json,
            node_id   uuid
        );"""
        )
        app.state._db = database
    except Exception as e:
        logger.exception(f"Failed to connect to database and create table: {e}")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.exception(f"Failed to disconnect from database: {e}")
