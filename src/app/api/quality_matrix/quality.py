import uuid

from app.api.quality_matrix.collections import collection_quality
from app.api.quality_matrix.models import Forms
from app.api.quality_matrix.replication_source import source_quality


async def quality(form: Forms, node_id: str):
    if form == Forms.REPLICATION_SOURCE:
        _quality, total = await source_quality(uuid.UUID(node_id))
    else:  # Forms.COLLECTIONS:
        _quality, total = await collection_quality(uuid.UUID(node_id))

    return _quality, total
