from typing import Mapping

from databases import Database
from sqlalchemy import select

from app.api.quality_matrix.models import Forms, Timeline


async def timestamps(database: Database, form: Forms):
    query = select([Timeline.timestamp]).where(Timeline.form == form)
    await database.connect()
    result: list[Mapping] = await database.fetch_all(query)

    return [entry["timestamp"] for entry in result]
