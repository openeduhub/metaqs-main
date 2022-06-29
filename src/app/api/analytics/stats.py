from uuid import UUID

from app.api.analytics.analytics import StatType


async def stats_latest(conn, stat_type: StatType, noderef_id: UUID) -> list[dict]:
    results = []
    print(conn, stat_type, noderef_id)
    results = [dict(record) for record in results]

    return results
