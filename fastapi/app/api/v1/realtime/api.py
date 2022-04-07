from fastapi import APIRouter

from .collections import router as collections_router
from .learning_materials import router as materials_router

router = APIRouter()
router.include_router(materials_router)
router.include_router(collections_router)
