from asyncpg import Pool
from fastapi import APIRouter, Depends, Security

from app.api.auth import authenticated
from app.pg.util import close_postgres_connection, get_postgres_async

from .analytics import router as analytics_router
from .background_tasks import router as background_tasks_router

router = APIRouter()


@router.get(
    "/pg-version",
    response_model=dict,
    dependencies=[Security(authenticated)],
    tags=["Healthcheck", "Authenticated"],
)
async def pg_version(
    pool: Pool = Depends(get_postgres_async),
):
    async with pool.acquire() as conn:
        version = await conn.fetchval("select version()")
        return {"version": version}


router.include_router(analytics_router)
router.include_router(background_tasks_router)

router.add_event_handler("shutdown", close_postgres_connection)
