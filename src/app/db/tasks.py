import uuid
from datetime import datetime

import sqlalchemy
from databases import Database
from fastapi import FastAPI

from app.api.quality_matrix.models import Forms, QualityOutput, Timeline
from app.core.logging import logger
from app.db.core import create_timeline_table, database_url, has_table


async def connect_to_db(app: FastAPI) -> None:
    database = Database(database_url(), min_size=2, max_size=10)

    try:
        await database.connect()
        app.state._db = database
    except Exception:
        logger.exception("")

    if not await has_table(Timeline.__tablename__):
        await create_timeline_table()


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception:
        logger.exception("")


async def store_in_timeline(
    data: list[QualityOutput],
    database: Database,
    form: Forms,
    node_id: uuid.UUID,
    total: dict,
):
    await database.connect()
    await database.execute(
        sqlalchemy.insert(Timeline).values(
            {
                "timestamp": datetime.now().timestamp(),
                "quality_matrix": data,
                "form": form,
                "node_id": node_id,
                "total": total,
            }
        )
    )
