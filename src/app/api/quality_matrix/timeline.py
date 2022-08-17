import uuid
from typing import Mapping

from databases import Database
from sqlalchemy import select

from app.api.quality_matrix.collections import collection_quality_matrix
from app.api.quality_matrix.models import Mode, Timeline
from app.api.quality_matrix.replication_source import source_quality_matrix
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.logging import logger
from app.db.tasks import store_in_timeline


async def quality_backup(database: Database):
    for mode in [Mode.REPLICATION_SOURCE, Mode.COLLECTIONS]:
        for node_id in COLLECTION_NAME_TO_ID.values():
            logger.info(f"Backing up for node id: '{node_id}'")
            if mode == Mode.REPLICATION_SOURCE:
                quality_data, total = await source_quality_matrix(uuid.UUID(node_id))
            else:  # Forms.COLLECTIONS:
                quality_data, total = await collection_quality_matrix(uuid.UUID(node_id))
            await store_in_timeline(
                quality_data, database, mode, uuid.UUID(node_id), total
            )


async def timestamps(database: Database, mode: Mode, node_id: uuid.UUID):
    query = (
        select([Timeline.timestamp])
        .where(Timeline.mode == mode)
        .where(Timeline.node_id == node_id)
    )
    await database.connect()
    result: list[Mapping] = await database.fetch_all(query)

    return [entry["timestamp"] for entry in result]
