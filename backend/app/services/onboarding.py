import re

from app.models.fpl_account import (
    FPLAccount,
)
from app.schemas.onboarding import (
    FPLTeamClaimResponse,
    FPLTeamPreviewResponse,
)
from app.services.fpl import (
    find_fpl_manager,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

FPL_ENTRY_PATTERN = re.compile(
    r"/entry/(\d+)(?:/|$)"
)


class InvalidFPLReferenceError(Exception):
    pass


class FPLTeamNotFoundError(Exception):
    pass


class FPLAccountTakenError(Exception):
    pass


class FPLAccountAlreadyLinkedError(Exception):
    pass


class FPLAccountClaimConflictError(Exception):
    pass


def extract_fpl_entry_id(
    reference: str,
) -> int:
    reference = reference.strip()

    if not reference:
        raise InvalidFPLReferenceError

    # Direct entry ID:
    #
    # 123456
    if reference.isdigit():
        entry_id = int(reference)

        if entry_id <= 0:
            raise InvalidFPLReferenceError

        return entry_id

    # FPL URL:
    #
    # https://fantasy.premierleague.com/
    # entry/123456/event/4
    match = FPL_ENTRY_PATTERN.search(
        reference
    )

    if match is None:
        raise InvalidFPLReferenceError

    entry_id = int(
        match.group(1)
    )

    if entry_id <= 0:
        raise InvalidFPLReferenceError

    return entry_id


async def preview_fpl_team(
    db: AsyncSession,
    *,
    user_id: int,
    reference: str,
) -> FPLTeamPreviewResponse:
    entry_id = extract_fpl_entry_id(
        reference
    )

    # External I/O first.
    manager = await find_fpl_manager(
        entry_id
    )

    if manager is None:
        raise FPLTeamNotFoundError

    linked_account = await db.scalar(
        select(FPLAccount).where(
            FPLAccount.fpl_entry_id
            == entry_id,
        )
    )

    if linked_account is None:
        available = True
        linked_to_current_user = False

    elif linked_account.user_id == user_id:
        available = True
        linked_to_current_user = True

    else:
        available = False
        linked_to_current_user = False

    return FPLTeamPreviewResponse(
        fpl_entry_id=entry_id,
        team_name=manager.team_name,
        manager_name=manager.manager_name,
        available=available,
        linked_to_current_user=(
            linked_to_current_user
        ),
    )


async def claim_fpl_team(
    db: AsyncSession,
    *,
    user_id: int,
    reference: str,
) -> FPLTeamClaimResponse:
    entry_id = extract_fpl_entry_id(
        reference
    )

    # Validate against FPL before opening a DB
    # transaction. We don't want to hold a DB
    # transaction while waiting for FPL.
    manager = await find_fpl_manager(
        entry_id
    )

    if manager is None:
        raise FPLTeamNotFoundError

    try:
        async with db.begin():
            current_account = await db.scalar(
                select(FPLAccount)
                .where(
                    FPLAccount.user_id
                    == user_id,
                )
                .with_for_update()
            )

            # Make retries idempotent.
            #
            # If the frontend sent the request
            # twice and this user already owns
            # this exact FPL entry, return it.
            if current_account is not None:
                if (
                    current_account.fpl_entry_id
                    == entry_id
                ):
                    return (
                        FPLTeamClaimResponse(
                            fpl_entry_id=(
                                current_account
                                .fpl_entry_id
                            ),
                            team_name=(
                                current_account
                                .team_name
                            ),
                            manager_name=(
                                current_account
                                .manager_name
                            ),
                            onboarding_required=False,
                        )
                    )

                raise (
                    FPLAccountAlreadyLinkedError
                )

            claimed_account = await db.scalar(
                select(FPLAccount)
                .where(
                    FPLAccount.fpl_entry_id
                    == entry_id,
                )
                .with_for_update()
            )

            if claimed_account is not None:
                raise FPLAccountTakenError

            account = FPLAccount(
                user_id=user_id,
                fpl_entry_id=entry_id,
                team_name=manager.team_name,
                manager_name=(
                    manager.manager_name
                ),
            )

            db.add(account)

            await db.flush()

    except (
        FPLAccountAlreadyLinkedError,
        FPLAccountTakenError,
    ):
        raise

    except IntegrityError as exc:
        # Protect against race conditions:
        #
        # User A and User B could theoretically
        # claim the same entry between our check
        # and INSERT.
        raise (
            FPLAccountClaimConflictError
        ) from exc

    return FPLTeamClaimResponse(
        fpl_entry_id=entry_id,
        team_name=manager.team_name,
        manager_name=manager.manager_name,
        onboarding_required=False,
    )