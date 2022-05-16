from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from starlette_context.middleware import RawContextMiddleware

from app.api.api import router
from app.core.config import ALLOWED_HOSTS, API_DEBUG, API_PORT, LOG_LEVEL, ROOT_PATH
from app.core.constants import OPEN_API_VERSION
from app.core.errors import http_422_error_handler, http_error_handler
from app.core.logging import logger
from app.elastic.utils import connect_to_elastic


def api() -> FastAPI:
    _api = FastAPI(
        root_path=ROOT_PATH,
        title="MetaQS API",
        version=OPEN_API_VERSION,
        debug=API_DEBUG,
    )
    logger.debug(f"Launching FastAPI on root path {ROOT_PATH}")

    _api.include_router(router)

    for route in _api.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name

    _api.add_middleware(RawContextMiddleware)

    _api.add_event_handler("startup", connect_to_elastic)

    _api.add_exception_handler(HTTPException, http_error_handler)
    _api.add_exception_handler(HTTP_422_UNPROCESSABLE_ENTITY, http_422_error_handler)

    return _api


load_dotenv()

app = CORSMiddleware(
    app=api(),
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
