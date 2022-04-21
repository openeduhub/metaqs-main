from importlib import import_module

from app.core.config import API_VERSION, ENABLE_ANALYTICS

from .util import PaginationParams, materials_filter_params, pagination_params

print(f"Current API_VERSION: {API_VERSION}")
if API_VERSION == "v1" or API_VERSION == "":
    from .v1 import real_time_router

    if ENABLE_ANALYTICS:
        from .v1 import analytics_router

real_time_router = real_time_router
if ENABLE_ANALYTICS:
    analytics_router = analytics_router
