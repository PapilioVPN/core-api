"""Administrator permission evaluation for HTTP and other app owners."""

from typing import Protocol

from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.auth.domain.results.identity import AdminIdentity


class IAdminAuthorizationService(Protocol):
    async def check(
        self, identity: AdminIdentity, scope: str, permission: AdminPermission
    ) -> AdminIdentity:
        """Require current eligibility and all requested permission bits.

        Args:
            identity: Verified access-token identity and scope snapshot.
            scope: Server-owned capability group required by the operation.
            permission: Read/create/update/delete bits required by the owner.

        Returns:
            The same identity after checks; token scopes are not recomputed.

        Raises:
            UnAuthorizedException: Current account or role is unavailable.
            ForbiddenException: Scope or required permission bits are absent.
        """
        ...
