import httpx

from app.integrations.fpl_rivals.constants import (
    FPL_RIVALS_BASE_URL,
    FPL_RIVALS_SEARCH_LIMIT,
    FPL_RIVALS_TIMEOUT_SECONDS,
)
from app.schemas.onboarding import FPLManagerSearchResult


class FPLManagerSearchUpstreamError(Exception):
    pass


_http_client: httpx.AsyncClient | None = None


def start_fpl_rivals_client() -> None:
    global _http_client

    if _http_client is not None:
        return

    _http_client = httpx.AsyncClient(
        base_url=FPL_RIVALS_BASE_URL,
        timeout=FPL_RIVALS_TIMEOUT_SECONDS,
    )


async def close_fpl_rivals_client() -> None:
    global _http_client

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _get_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("FPL Rivals HTTP client is not initialized")

    return _http_client


async def search_fpl_managers(
    query: str,
) -> list[FPLManagerSearchResult]:
    try:
        response = await _get_client().get(
            "/search",
            params={
                "q": query,
                "type": "manager",
                "limit": FPL_RIVALS_SEARCH_LIMIT,
            },
        )
        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise FPLManagerSearchUpstreamError(
            "Manager search provider is unavailable"
        ) from exc

    try:
        payload = response.json()
        managers = payload["data"]["managers"]

        if not isinstance(managers, list):
            raise TypeError

        results: list[FPLManagerSearchResult] = []

        for manager in managers[:FPL_RIVALS_SEARCH_LIMIT]:
            entry_id = manager["id"]
            manager_name = manager["player_name"]
            team_name = manager["entry_name"]

            if (
                isinstance(entry_id, bool)
                or not isinstance(entry_id, int)
                or entry_id <= 0
                or not isinstance(manager_name, str)
                or not isinstance(team_name, str)
            ):
                raise TypeError

            results.append(
                FPLManagerSearchResult(
                    entry_id=entry_id,
                    manager_name=manager_name,
                    team_name=team_name,
                )
            )

        return results

    except (KeyError, TypeError, ValueError) as exc:
        raise FPLManagerSearchUpstreamError(
            "Manager search provider returned an unexpected payload"
        ) from exc
