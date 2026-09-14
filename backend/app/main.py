import logging
from contextlib import asynccontextmanager

from app.api.router import api_router
from app.core.redis import (
    close_redis,
    initialize_redis,
)
from app.core.scheduler import (
    start_scheduler,
    stop_scheduler,
)
from app.integrations.fpl.client import (
    FPLUpstreamError,
    close_fpl_client,
    get_bootstrap_static,
    start_fpl_client,
)
from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    await initialize_redis()

    start_fpl_client()

    # Prime bootstrap metadata, but don't prevent
    # Rivalxi from starting if FPL is temporarily down.
    try:
        await get_bootstrap_static()

    except FPLUpstreamError:
        logger.warning(
            "Unable to warm FPL bootstrap cache"
        )

    start_scheduler()

    yield

    stop_scheduler()

    await close_fpl_client()
    await close_redis()


app = FastAPI(
    title="Rivalxi API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(
    api_router,
    prefix="/api/v1",
)