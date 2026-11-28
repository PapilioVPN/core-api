"""Enforce the read grant on routing observations and simulations."""

from typing import Annotated

from fastapi import Depends

from src.apps.core.access.auth.app.validators.authorization import (
    validate_admin_permission,
)
from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)


async def require_routing_read(
    identity: Annotated[AdminIdentity, Depends(current_admin)],
) -> None:
    validate_admin_permission(identity, "network", AdminPermission.READ)
