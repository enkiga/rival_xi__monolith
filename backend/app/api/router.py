from app.api.v1.auth import router as auth_router
from app.api.v1.fpl import router as fpl_router
from app.api.v1.health import router as health_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.league import router as league_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.onboarding import router as onboarding_router
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

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"],
)

api_router.include_router(
    onboarding_router,
    prefix="/onboarding",
    tags=["Onboarding"],
)

api_router.include_router(
    invitations_router,
    tags=["Invitations"],
)
api_router.include_router(
    notifications_router,
    prefix="/notifications",
    tags=["Notifications"],
)
