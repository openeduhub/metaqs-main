from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from starlette_context.middleware import RawContextMiddleware

import app.api as api
from app.api.languagetool.api import router as languagetool_router
from app.core.config import (
    ALLOWED_HOSTS,
    BACKGROUND_TASK_ANALYTICS_INTERVAL,
    BACKGROUND_TASK_SEARCH_STATS_INTERVAL,
    BACKGROUND_TASK_SPELLCHECK_INTERVAL,
    DEBUG,
    ENABLE_ANALYTICS,
    LOG_LEVEL,
    PROJECT_NAME,
    ROOT_PATH,
)
from app.core.errors import http_422_error_handler, http_error_handler
from app.core.logging import logger
from app.elastic.utils import close_elastic_connection, connect_to_elastic
from app.http import close_client

API_PORT = 8081

OPEN_API_VERSION = "2.1.0"
fastapi_app = FastAPI(
    root_path=ROOT_PATH,
    title=f"{PROJECT_NAME} API",
    description=f"""
* [**Analytics API**]({ROOT_PATH}/analytics/docs)
* [**LanguageTool API**]({ROOT_PATH}/languagetool/docs)
    """,
    version=OPEN_API_VERSION,
    debug=DEBUG,
)
logger.debug(f"Launching FastAPI on root path {ROOT_PATH}")


class Ping(BaseModel):
    status: str = Field(
        default="not ok",
        description="Ping output. Should be 'ok' in happy case.",
    )


@fastapi_app.get(
    "/_ping",
    description="Ping function for automatic health check.",
    response_model=Ping,
    tags=["Healthcheck"],
)
async def ping_api():
    return {"status": "ok"}


fastapi_app.include_router(api.real_time_router, prefix="/real-time")

if ENABLE_ANALYTICS:
    analytics_app = FastAPI(
        title=f"{PROJECT_NAME} Analytics API",
        description=f"""* [**Real-Time API**]({ROOT_PATH}/docs)
    * [**LanguageTool API**]({ROOT_PATH}/languagetool/docs)
        """,
        version=OPEN_API_VERSION,
        debug=DEBUG,
    )
    analytics_app.include_router(api.analytics_router)
    fastapi_app.mount(path="/analytics", app=analytics_app)

languagetool_app = FastAPI(
    title=f"{PROJECT_NAME} LanguageTool API",
    description=f"""* [**Real-Time API**]({ROOT_PATH}/docs)
* [**Analytics API**]({ROOT_PATH}/analytics/docs)
    """,
    debug=DEBUG,
    version=OPEN_API_VERSION,
)
languagetool_app.include_router(languagetool_router)
fastapi_app.mount(path="/languagetool", app=languagetool_app)

for route in fastapi_app.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name

fastapi_app.add_middleware(RawContextMiddleware)

fastapi_app.add_event_handler("startup", connect_to_elastic)
fastapi_app.add_event_handler("shutdown", close_elastic_connection)

if ENABLE_ANALYTICS:
    from app.analytics.analytics import background_task as analytics_background_task
    from app.analytics.search_stats import (
        background_task as search_stats_background_task,
    )
    from app.analytics.spellcheck import background_task as spellcheck_background_task

    if BACKGROUND_TASK_ANALYTICS_INTERVAL:
        fastapi_app.add_event_handler("startup", analytics_background_task)
    if BACKGROUND_TASK_SEARCH_STATS_INTERVAL:
        fastapi_app.add_event_handler("startup", search_stats_background_task)
    if BACKGROUND_TASK_SPELLCHECK_INTERVAL:
        fastapi_app.add_event_handler("startup", spellcheck_background_task)

fastapi_app.add_exception_handler(HTTPException, http_error_handler)
fastapi_app.add_exception_handler(HTTP_422_UNPROCESSABLE_ENTITY, http_422_error_handler)

fastapi_app.add_event_handler("shutdown", close_client)

app = CORSMiddleware(
    app=fastapi_app,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

if __name__ == "__main__":
    import os

    import uvicorn

    conf = {
        "host": "0.0.0.0",
        "port": API_PORT,
        "reload": True,
        "reload_dirs": [f"{os.getcwd()}/app"],
        "log_level": LOG_LEVEL,
    }
    print(f"starting uvicorn with config: {conf}")

    uvicorn.run("app.main:app", **conf)
