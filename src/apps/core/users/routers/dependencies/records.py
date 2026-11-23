"""Account path ownership and supported HTTP profile edits."""

from typing import Annotated

from fastapi import Depends
from papilio.types.aliases import IdType

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.auth.routers.dependencies.identity import current_admin
from src.apps.core.users.app.validators.profile import (
    validate_contact_fields,
    validate_self_account,
)
from src.apps.core.users.domain.dtos.records import UserUpdate


async def current_account(
    id: IdType, identity: Annotated[AdminIdentity, Depends(current_admin)]
) -> AdminIdentity:
    """Require the signed-in account named by the user path.

    Args:
        id: Internal target ID validated through native ID validation.
        identity: Verified access identity.

    Returns:
        The same authenticated identity when the target matches it.

    Raises:
        ForbiddenException: The target belongs to another account.
    """
    validate_self_account(identity.user_id, id)
    return identity


async def user_profile_patch(data: UserUpdate) -> UserUpdate:
    """Reject contact fields before the existing profile write is called.

    Args:
        data: Native body preserving omitted and explicit-null fields.

    Returns:
        The same DTO instance without another validation/conversion round trip.

    Raises:
        ValidationException: Mobile or email was explicitly supplied.
    """
    validate_contact_fields(data)
    return data
