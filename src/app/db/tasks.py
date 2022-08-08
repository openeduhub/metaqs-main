import uuid
from datetime import datetime

import sqlalchemy
from databases import Database
from fastapi import FastAPI

from app.api.quality_matrix.models import Mode, QualityOutput, Timeline
from app.core.logging import logger
from app.db.core import database_url


async def connect_to_db(app: FastAPI) -> None:
    database = Database(database_url(), min_size=2, max_size=10)

    try:
        await database.connect()
        app.state._db = database
    except Exception:
        logger.exception("")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception:
        logger.exception("")


async def store_in_timeline(
    data: list[QualityOutput],
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
