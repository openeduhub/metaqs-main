from typing import Mapping

from databases import Database
from sqlalchemy import select

from app.api.quality_matrix.models import Timeline


async def timestamps(database: Database):
    s = select([Timeline.timestamp])
    await database.connect()
    result: list[Mapping] = await database.fetch_all(s)

    return [entry["timestamp"] for entry in result]
