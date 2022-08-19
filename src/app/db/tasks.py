import uuid
from datetime import datetime

import sqlalchemy
from databases import Database
from fastapi import FastAPI

from app.api.quality_matrix.models import Mode, Timeline, QualityMatrixRow
from app.core.logging import logger
from app.db.core import database_url


async def connect_to_db(app: FastAPI) -> None:
    logger.info("Instantiating database")
    database = Database(database_url(), min_size=2, max_size=10)

    try:
        await database.connect()
        await database.execute('''
        create table if not exists timeline
        (
            id        int,
            timestamp int,
            mode      text,
            quality   json,
            total     json,
            node_id   uuid
        );''')
        app.state._db = database
    except Exception as e:
        logger.exception(f"Failed to connect to database and create table: {e}")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.exception(f"Failed to disconnect from database: {e}")


async def store_in_timeline(
    data: list[QualityMatrixRow],
    database: Database,
    mode: Mode,
    node_id: uuid.UUID,
    total: dict,
):
    await database.connect()
    await database.execute(
        sqlalchemy.insert(Timeline).values(
            {
                "timestamp": datetime.now().timestamp(),
                "quality": [
                    {
                        "row_header": entry.row_header,
                        "level": entry.level,
                        "columns": entry.columns,
                    }
                    for entry in data
                ],
                "mode": mode,
                "node_id": node_id,
                "total": total,
            }
        )
    )
