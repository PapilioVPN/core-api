"""List and close sessions owned by the authenticated administrator."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta

from src.apps.core.access.auth.app.interfaces.commands import ISessionCommand
from src.apps.core.access.auth.app.interfaces.services import ISessionService
from src.apps.core.access.auth.domain.dtos.sessions import SessionList
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.core.access.auth.routers.schemas.sessions import (
    RevokedOutput,
    SessionOutput,
)

router = APIRouter(
    prefix="/admin/account/me/sessions",
    route_class=DishkaRoute,
)

CurrentAdmin = Annotated[AdminIdentity, Depends(current_admin)]


@router.get("", response_model=APIResponse[SessionOutput, PagerMeta])
async def get_sessions(
    identity: CurrentAdmin,
    query: Annotated[SessionList, Query()],
    service: FromDishka[ISessionService],
) -> APIResponse[SessionOutput, PagerMeta]:
    """Read a page of active sessions, marking the current session."""
    page = await service.list(identity, query)
    return APIResponse[SessionOutput, PagerMeta](
        success=True,
        data=SessionOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.delete("", response_model=APIResponse[RevokedOutput, None])
async def delete_sessions(
    identity: CurrentAdmin,
    command: FromDishka[ISessionCommand],
) -> APIResponse[RevokedOutput, None]:
    """Close all other active sessions and return their count."""
    count = await command.revoke_others(identity)
    return APIResponse[RevokedOutput, None].from_data(
        RevokedOutput(count=count)
    )


@router.delete("/{id}", response_model=APIResponse[None, None])
async def delete_session(
    id: UUID,
    identity: CurrentAdmin,
    command: FromDishka[ISessionCommand],
) -> APIResponse[None, None]:
    """Close one owned session, including the current session."""
    await command.revoke_one(identity, id)
    return APIResponse[None, None](success=True)
