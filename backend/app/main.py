from contextlib import asynccontextmanager

from app.api.router import api_router
from app.core.scheduler import (
    start_scheduler,
    stop_scheduler,
)
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    start_scheduler()

    yield

    stop_scheduler()


app = FastAPI(
    title="Rivalxi API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(
    api_router,
    prefix="/api/v1",
)