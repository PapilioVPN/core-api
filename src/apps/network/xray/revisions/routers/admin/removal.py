"""Remove unused revision records through authorized Panel operations."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.app.validators.authorization import (
    validate_admin_permission,
)
from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)

from ...app.interfaces.records import IXrayRevisionService
from ...domain.dtos.records import XrayRevisionBulkRemoveInput
from ..schemas.removal import XrayRevisionRemovalOutput


async def _require_delete(
    identity: Annotated[AdminIdentity, Depends(current_admin)],
) -> None:
    validate_admin_permission(identity, "network", AdminPermission.DELETE)


router = APIRouter(
    prefix="/admin/xray/revisions",
    route_class=DishkaRoute,
    dependencies=[Depends(_require_delete)],
)


@router.delete("/{id:int}", status_code=204)
async def delete_revision(
    id: IdType, revisions: FromDishka[IXrayRevisionService]
) -> Response:
    await revisions.remove(id)
    return Response(status_code=204)


@router.post("/bulk/delete")
async def delete_revisions(
    data: XrayRevisionBulkRemoveInput,
    revisions: FromDishka[IXrayRevisionService],
) -> APIResponse[XrayRevisionRemovalOutput, None]:
    results = await revisions.remove_many(data)
    return APIResponse[XrayRevisionRemovalOutput, None].from_data(
        XrayRevisionRemovalOutput.from_objs(results)
    )
