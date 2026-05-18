import importlib

from fastapi import APIRouter

from app.features.navigation.router import router as navigation_router
from app.features.localization.router import router as localization_router

api_router = APIRouter()
api_router.include_router(navigation_router)
import_router = importlib.import_module("app.features.import.router").router
api_router.include_router(import_router)
api_router.include_router(localization_router)
