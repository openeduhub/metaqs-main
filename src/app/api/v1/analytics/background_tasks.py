from fastapi import APIRouter, BackgroundTasks, Security
from starlette.status import HTTP_202_ACCEPTED

import app.analytics.analytics as analytics
import app.analytics.search_stats as search_stats
from app.api.auth import authenticated

router = APIRouter()


@router.post(
    "/run-analytics",
    dependencies=[Security(authenticated)],
    status_code=HTTP_202_ACCEPTED,
    tags=["Background Tasks", "Authenticated"],
)
async def run_analytics(*, background_tasks: BackgroundTasks):
    background_tasks.add_task(analytics.run)


@router.post(
    "/run-search-stats",
    dependencies=[Security(authenticated)],
    status_code=HTTP_202_ACCEPTED,
    tags=["Background Tasks", "Authenticated"],
)
async def run_search_stats(*, background_tasks: BackgroundTasks):
    background_tasks.add_task(search_stats.run)
