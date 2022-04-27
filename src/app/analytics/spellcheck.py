from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sapg
from fastapi_utils.tasks import repeat_every
from pylanguagetool import api as languagetool

from app.core.config import (
    BACKGROUND_TASK_SPELLCHECK_INTERVAL,
    DEBUG,
    LANGUAGETOOL_ENABLED_CATEGORIES,
    LANGUAGETOOL_URL,
)
from app.core.logging import logger
from app.pg.metadata import spellcheck, spellcheck_queue
from app.pg.util import get_postgres


@repeat_every(seconds=BACKGROUND_TASK_SPELLCHECK_INTERVAL, logger=logger)
def background_task():
    run()


def run():
    logger.info(f"Spellcheck: starting processing at: {datetime.now()}")

    with next(get_postgres()) as session:
        rows = list(session.execute(sa.select(spellcheck_queue)))

        logger.debug(f"Spellcheck: {len(rows)} retrieved")

        for i, row in enumerate(rows):
            response = _spellcheck(row.text_content)

            if "matches" in response and response["matches"]:

                if DEBUG:
                    logger.debug(f"Spellcheck: found error for row: {row}")

                t = spellcheck
                stmt = sapg.insert(t).values(
                    resource_id=row.resource_id,
                    resource_type=row.resource_type,
                    resource_field=row.resource_field,
                    text_content=row.text_content,
                    derived_at=row.derived_at,
                    error=response,
                )
                session.execute(
                    stmt.on_conflict_do_update(
                        index_elements=[t.c.resource_id, t.c.resource_field],
                        set_=dict(
                            text_content=stmt.excluded.text_content,
                            derived_at=stmt.excluded.derived_at,
                            error=stmt.excluded.error,
                        ),
                    )
                )

            session.execute(
                sa.delete(spellcheck_queue)
                .where(spellcheck_queue.c.resource_id == row.resource_id)
                .where(spellcheck_queue.c.resource_field == row.resource_field)
            )

            if i > 0 and i % 100 == 0:
                session.commit()
                logger.info(f"Spellcheck: {i} spellchecks completed")

        session.commit()

    logger.info(f"Spellcheck: processing finished at: {datetime.now()}")


def _spellcheck(text, lang="de-DE"):
    response = languagetool.check(
        text,
        api_url=f"{LANGUAGETOOL_URL}/",
        lang=lang,
        enabled_categories=",".join(LANGUAGETOOL_ENABLED_CATEGORIES),
        enabled_only=True,
    )

    return response
