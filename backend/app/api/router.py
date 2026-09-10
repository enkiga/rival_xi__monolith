from app.api.v1.fpl import router as fpl_router
from app.api.v1.health import router as health_router
from app.api.v1.league import router as league_router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(
    health_router,
    tags=["Health"],
)
api_router.include_router(
    fpl_router,
    prefix="/fpl",
    tags=["FPL"],
)
api_router.include_router(
    league_router,
    prefix="/leagues",
    tags=["Leagues"],
)
