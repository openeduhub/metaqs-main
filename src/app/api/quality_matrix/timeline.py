from typing import Mapping

from databases import Database
from sqlalchemy import select

from app.api.quality_matrix.models import Timeline
from app.db.core import create_timeline_table, has_table


async def timestamps(database: Database):
    if not await has_table("timeline"):
        await create_timeline_table()

    s = select([Timeline.timestamp])
    await database.connect()
    result: list[Mapping] = await database.fetch_all(s)

    if result is None:
        return []
    return [entry.timestamp for entry in result]
