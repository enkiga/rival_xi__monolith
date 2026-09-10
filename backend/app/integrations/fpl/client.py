import httpx
from app.integrations.fpl.constants import FPL_BASE_URL


async def get_fpl_entry(entry_id: int) -> dict | None:
    async with httpx.AsyncClient(
        base_url=FPL_BASE_URL,
        timeout=10.0,
    ) as client:
        response = await client.get(f"/entry/{entry_id}/")

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return response.json()

async def get_bootstrap_static() -> dict:
    async with httpx.AsyncClient(
        base_url=FPL_BASE_URL,
        timeout=10.0,
    ) as client:
        response = await client.get(
            "/bootstrap-static/"
        )

        response.raise_for_status()

        return response.json()

async def get_entry_gameweek_picks(
    entry_id: int,
    gameweek: int,
) -> dict | None:
    async with httpx.AsyncClient(
        base_url=FPL_BASE_URL,
        timeout=10.0,
    ) as client:
        response = await client.get(
            f"/entry/{entry_id}/event/{gameweek}/picks/"
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return response.json()

async def get_event_live(
    gameweek: int,
) -> dict:
    async with httpx.AsyncClient(
        base_url=FPL_BASE_URL,
        timeout=10.0,
    ) as client:
        response = await client.get(
            f"/event/{gameweek}/live/"
        )

        response.raise_for_status()

        return response.json()