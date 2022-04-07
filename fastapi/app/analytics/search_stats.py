from datetime import datetime
from time import sleep

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sapg
from fastapi_utils.tasks import repeat_every

from app.core.config import (
    BACKGROUND_TASK_SEARCH_STATS_INTERVAL,
    BACKGROUND_TASK_SEARCH_STATS_SLEEP_INTERVAL,
)
from app.core.logging import logger
from app.crud.stats import search_hits_by_material_type
from app.pg.metadata import Collection, ResourceField, ResourceType, search_stats
from app.pg.util import get_postgres


@repeat_every(seconds=BACKGROUND_TASK_SEARCH_STATS_INTERVAL, logger=logger)
def background_task():
    run()


def run():
    now = datetime.now()
    logger.info(f"Search stats: starting processing at: {now}")

    with next(get_postgres()) as session:
        c_title = sa.literal_column("doc -> 'properties' ->> 'cm:title'").label("title")
        for i, row in enumerate(
            session.execute(
                sa.select(Collection.__table__.c.id, c_title).where(c_title.isnot(None))
            )
        ):
            sleep(BACKGROUND_TASK_SEARCH_STATS_SLEEP_INTERVAL)
            stats = search_hits_by_material_type(row.title)

            stmt = sapg.insert(search_stats).values(
                resource_id=row.id,
                resource_field=ResourceField.TITLE,
                resource_type=ResourceType.COLLECTION,
                searchtext=row.title,
                derived_at=now,
                stats=stats,
            )
            session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[
                        search_stats.c.resource_id,
                        search_stats.c.resource_field,
                    ],
                    set_=dict(
                        searchtext=stmt.excluded.searchtext,
                        derived_at=stmt.excluded.derived_at,
                        stats=stmt.excluded.stats,
                    ),
                )
            )

            if i > 0 and i % 100 == 0:
                session.commit()
                logger.info(f"Search stats: {i} stats completed")

        session.commit()

    logger.info(f"Search stats: processing finished at: {datetime.now()}")
