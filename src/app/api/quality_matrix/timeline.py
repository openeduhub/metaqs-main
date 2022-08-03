import uuid
from typing import Mapping

from databases import Database
from sqlalchemy import select

from app.api.quality_matrix.collections import collection_quality
from app.api.quality_matrix.models import Forms, TimelineNew
from app.api.quality_matrix.replication_source import source_quality
from app.core.constants import COLLECTION_NAME_TO_ID
from app.db.tasks import store_in_timeline


async def quality_backup(database: Database):
    for form in [Forms.REPLICATION_SOURCE, Forms.COLLECTIONS]:
        for node_id in COLLECTION_NAME_TO_ID.values():
            print(node_id)
            if form == Forms.REPLICATION_SOURCE:
                quality_data, total = await source_quality(uuid.UUID(node_id))
            else:  # Forms.COLLECTIONS:
                quality_data, total = await collection_quality(uuid.UUID(node_id))
            await store_in_timeline(
                quality_data, database, form, uuid.UUID(node_id), total
            )


async def timestamps(database: Database, form: Forms, node_id: uuid.UUID):
    query = (
        select([TimelineNew.timestamp])
        .where(TimelineNew.form == form)
        .where(TimelineNew.node_id == node_id)
    )
    await database.connect()
    result: list[Mapping] = await database.fetch_all(query)

    return [entry["timestamp"] for entry in result]
