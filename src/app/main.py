from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from starlette_context.middleware import RawContextMiddleware

from app.api.api import router
from app.core.config import ALLOWED_HOSTS, DEBUG, LOG_LEVEL, PROJECT_NAME, ROOT_PATH
from app.core.errors import http_422_error_handler, http_error_handler
from app.core.logging import logger
from app.elastic.utils import close_elastic_connection, connect_to_elastic
from app.http_client import close_client

API_PORT = 8081

OPEN_API_VERSION = "2.1.0"
fastapi_app = FastAPI(
    root_path=ROOT_PATH,
    title=f"{PROJECT_NAME} API",
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


fastapi_app.include_router(router, prefix="/real-time")

for route in fastapi_app.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name

fastapi_app.add_middleware(RawContextMiddleware)

fastapi_app.add_event_handler("startup", connect_to_elastic)
fastapi_app.add_event_handler("shutdown", close_elastic_connection)

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
