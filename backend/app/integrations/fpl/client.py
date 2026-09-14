import asyncio

import httpx
from app.core.cache import (
    get_cached_json,
    set_cached_json,
)
from app.core.config import settings
from app.integrations.fpl.constants import (
    FPL_BASE_URL,
)
from app.integrations.fpl.rate_limit import (
    wait_for_fpl_request_slot,
)
from redis.exceptions import RedisError


class FPLUpstreamError(Exception):
    pass


_http_client: httpx.AsyncClient | None = None


def start_fpl_client() -> None:
    global _http_client

    if _http_client is not None:
        return

    _http_client = httpx.AsyncClient(
        base_url=FPL_BASE_URL,
        timeout=10.0,
    )


async def close_fpl_client() -> None:
    global _http_client

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _get_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("FPL HTTP client is not initialized")

    return _http_client


def _retry_delay(
    response: httpx.Response,
    attempt: int,
) -> float:
    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass

    return min(
        2**attempt,
        30,
    )


async def _get_json(
    path: str,
    *,
    cache_key: str,
    cache_ttl: int,
    allow_not_found: bool = False,
) -> dict | None:
    cached = await get_cached_json(cache_key)

    if cached is not None:
        return cached

    client = _get_client()

    for attempt in range(settings.fpl_max_retries + 1):
        try:
            await wait_for_fpl_request_slot()

        except RedisError as exc:
            raise FPLUpstreamError(
                "FPL request pacing is unavailable"
            ) from exc

        try:
            response = await client.get(path)

        except httpx.RequestError as exc:
            if attempt >= settings.fpl_max_retries:
                raise FPLUpstreamError("Unable to reach FPL") from exc

            await asyncio.sleep(min(2**attempt, 30))

            continue

        if response.status_code == 404 and allow_not_found:
            return None

        if response.status_code in {
            429,
            500,
            502,
            503,
            504,
        }:
            if attempt >= settings.fpl_max_retries:
                raise FPLUpstreamError("FPL is temporarily unavailable")

            await asyncio.sleep(
                _retry_delay(
                    response,
                    attempt,
                )
            )

            continue

        try:
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise FPLUpstreamError(
                f"Unexpected FPL response: {response.status_code}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise FPLUpstreamError(
                "FPL returned invalid JSON"
            ) from exc

        if not isinstance(data, dict):
            raise FPLUpstreamError(
                "FPL returned an unexpected payload"
            )

        await set_cached_json(
            key=cache_key,
            value=data,
            ttl=cache_ttl,
        )

        return data

    raise FPLUpstreamError("FPL request failed")


async def get_bootstrap_static() -> dict:
    data = await _get_json(
        "/bootstrap-static/",
        cache_key=("rivalxi:v1:fpl:bootstrap"),
        cache_ttl=(settings.fpl_bootstrap_cache_ttl),
    )

    if data is None:
        raise FPLUpstreamError("Bootstrap data unavailable")

    return data


async def get_cached_bootstrap_static() -> dict | None:
    return await get_cached_json("rivalxi:v1:fpl:bootstrap")


async def get_fpl_entry(
    entry_id: int,
) -> dict | None:
    return await _get_json(
        f"/entry/{entry_id}/",
        cache_key=(f"rivalxi:v1:fpl:entry:{entry_id}"),
        cache_ttl=(settings.fpl_entry_cache_ttl),
        allow_not_found=True,
    )


async def get_entry_gameweek_picks(
    entry_id: int,
    gameweek: int,
) -> dict | None:
    return await _get_json(
        (f"/entry/{entry_id}/event/{gameweek}/picks/"),
        cache_key=(f"rivalxi:v1:fpl:entry:{entry_id}:gw:{gameweek}:picks"),
        cache_ttl=(settings.fpl_picks_cache_ttl),
        allow_not_found=True,
    )


async def get_event_live(
    gameweek: int,
) -> dict:
    data = await _get_json(
        f"/event/{gameweek}/live/",
        cache_key=(f"rivalxi:v1:fpl:gw:{gameweek}:live"),
        cache_ttl=(settings.fpl_live_cache_ttl),
    )

    if data is None:
        raise FPLUpstreamError("Live gameweek data unavailable")

    return data
