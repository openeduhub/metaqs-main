import os
from datetime import datetime

from fastapi_utils.tasks import repeat_every
from sqlalchemy.orm import Session

import app.analytics.rpc_client as dbt
from app.core.config import BACKGROUND_TASK_ANALYTICS_INTERVAL
from app.core.logging import logger
from app.pg.util import get_postgres

from .resource_import import import_collections, import_materials


@repeat_every(seconds=BACKGROUND_TASK_ANALYTICS_INTERVAL, logger=logger)
def background_task():
    run()


def run():
    derived_at = datetime.now()

    logger.info(f"{os.getpid()}: Starting analytics import at: {derived_at}")

    with next(get_postgres()) as session:
        _backup_previous_run(session)

        import_collections(session=session, derived_at=derived_at)
        logger.info(
            f"Analytics: after collections import: {len(session.new)} resources added to session"
        )

        import_materials(session=session, derived_at=derived_at)
        logger.info(
            f"Analytics: after materials import: {len(session.new)} resources added to session"
        )

        session.commit()

    logger.info(f"Finished analytics import at: {datetime.now()}")

    result = dbt.run_analytics()
    logger.info(f"Analytics: run started {result}")
    #
    result = dbt.poll(request_token=result["request_token"])
    logger.info(f"Analytics: run took: {result.get('elapsed')}")


def _backup_previous_run(session: Session):
    logger.info(f"Analytics: copying previous import data to backup tables")

    session.execute(
        """
        drop table if exists raw.collections_previous_run cascade;
        create table raw.collections_previous_run
        as table raw.collections;
        truncate raw.collections;
        """
    )
    logger.info(f"Analytics: copied collections to collections_previous_run")

    session.execute(
        """
        drop table if exists raw.materials_previous_run cascade;
        create table raw.materials_previous_run
        as table raw.materials;
        truncate raw.materials;
        """
    )
    logger.info(f"Analytics: copied materials to materials_previous_run")
