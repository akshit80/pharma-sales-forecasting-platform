from fastapi import APIRouter
from backend.api.datasets import router as datasets_router
from backend.api.eda import router as eda_router
from backend.api.forecast import router as forecast_router
from backend.api.scenarios import router as scenarios_router
from backend.api.reports import router as reports_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(datasets_router)
api_router.include_router(eda_router)
api_router.include_router(forecast_router)
api_router.include_router(scenarios_router)
api_router.include_router(reports_router)
