from fastapi import APIRouter

from app.core.config import ENABLE_MATERIALS_API

from .collections import router as collections_router
from .learning_materials import router as materials_router

real_time_router = APIRouter()
if ENABLE_MATERIALS_API:
    real_time_router.include_router(materials_router)
real_time_router.include_router(collections_router)
