"""Verify the card transfer hook's API key at the HTTP boundary."""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Security
from fastapi.security import APIKeyHeader
from papilio.errors.exceptions import UnAuthorizedException

from ...app.interfaces.services import IAPIKeyService


@inject
async def require_api_key(
    key: Annotated[
        str | None, Security(APIKeyHeader(name="X-API-Key", auto_error=False))
    ],
    service: FromDishka[IAPIKeyService],
) -> int:
    """Return the verified identity without retaining the presented secret."""
    id = await service.verify(key) if key is not None else None
    if id is None:
        raise UnAuthorizedException(
            message="Invalid card transfer API key.",
            message_code="card_api_key_invalid",
        )
    return id
