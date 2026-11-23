"""Coordinate validated role/scope ownership and assignment writes."""

from collections.abc import Sequence

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import BatchResultType

from src.apps.core.audit.app.interfaces.records import IAuditWriter
from src.apps.core.audit.domain.dtos.event import AuditEvent
from src.apps.core.audit.domain.enums.actions import AuditAction
from src.apps.core.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.roles.app.validators.role_scopes import (
    RoleScopeChecks,
)
from src.apps.core.roles.domain.dtos.role_scopes import (
    RoleScopeBatchCreate,
    RoleScopeBatchUpdate,
    RoleScopeCreate,
    RoleScopeUpdate,
)
from src.apps.core.roles.domain.models.records import RoleScopeModel
from src.apps.core.scopes.app.interfaces.services import IScopeService


def _event(action: AuditAction, row: RoleScopeModel) -> AuditEvent:
    """Capture the exact assignment returned by the mutation."""
    return AuditEvent(
        action,
        row.id,
        role_id=row.role_id,
        scope_id=row.scope_id,
        permissions=row.permissions,
    )


class RoleScopeCommand(RoleScopeChecks):
    def __init__(
        self,
        roles: IRoleService,
        scopes: IScopeService,
        assignments: IRoleScopeService,
        audit: IAuditWriter,
    ) -> None:
        """Bind service contracts sharing the native request transaction.

        Args:
            roles: Owner of authoritative role existence checks.
            scopes: Owner of authoritative scope existence reads.
            assignments: Owner of assignment reads and native bulk writes.
            audit: Audit writer on the same transaction.

        Returns:
            None.
        """
        self.roles = roles
        self.scopes = scopes
        self.assignments = assignments
        self.audit = audit

    @transactional
    async def create(
        self, role_id: int, data: RoleScopeCreate, *, actor_id: int
    ) -> RoleScopeModel:
        """Assign a scope after verifying both referenced owners.

        Args:
            role_id: Parent role identity from the path.
            data: Scope identity and permissions from the body.
            actor_id: Verified operator making the assignment.

        Returns:
            The created assignment, including a zero mask.

        Raises:
            NotFoundException: The role or scope does not exist.
            ConflictException: The pair is already assigned.
        """
        await self.roles.get_by_id(role_id)
        await self.scopes.get_by_id(data.scope_id)
        row = await self.assignments.create(role_id, data)
        await self.audit.record(
            actor_id, _event(AuditAction.ROLE_SCOPE_CREATE, row)
        )
        return row

    @transactional
    async def update(
        self, role_id: int, data: RoleScopeUpdate, *, actor_id: int
    ) -> RoleScopeModel:
        """Replace one assigned mask after checking its referenced owners.

        Args:
            role_id: Parent role identity from the path.
            data: Scope identity and replacement mask from the body.
            actor_id: Verified operator changing the mask.

        Returns:
            The updated assignment within this role only.

        Raises:
            NotFoundException: The role, scope or assignment is absent.
        """
        await self.roles.get_by_id(role_id)
        await self.scopes.get_by_id(data.scope_id)
        row = await self.assignments.update(role_id, data)
        await self.audit.record(
            actor_id, _event(AuditAction.ROLE_SCOPE_UPDATE, row)
        )
        return row

    @transactional
    async def remove(
        self, role_id: int, scope_id: int, *, actor_id: int
    ) -> RoleScopeModel:
        """Remove one assignment after checking its referenced owners.

        Args:
            role_id: Parent role identity from the path.
            scope_id: Scope identity supplied by the adapter.
            actor_id: Verified operator removing the assignment.

        Returns:
            The removed assignment, preserving its role and shared scope.

        Raises:
            NotFoundException: The role, scope or assignment is absent.
        """
        await self.roles.get_by_id(role_id)
        await self.scopes.get_by_id(scope_id)
        row = await self.assignments.remove(role_id, scope_id)
        await self.audit.record(
            actor_id, _event(AuditAction.ROLE_SCOPE_REMOVE, row)
        )
        return row

    @transactional
    async def create_batch(
        self, role_id: int, data: RoleScopeBatchCreate, *, actor_id: int
    ) -> BatchResultType[RoleScopeModel, ValidationException]:
        """Pre-read references and insert only valid new assignments in bulk.

        Args:
            role_id: Parent role checked once through its owning service.
            data: One to 100 scope/mask inputs; first duplicate wins selection.
            actor_id: Verified operator making the assignments.

        Returns:
            Created records in input order and indexed errors for rejected
            items. All-invalid input returns errors without performing a write.

        Raises:
            NotFoundException: The parent role does not exist.
            ConflictException: A conflicting insert occurred after the read.
        """
        await self.roles.get_by_id(role_id)
        ids = [item.scope_id for item in data.items]
        scopes = await self.scopes.get_by_ids(ids)
        existing = await self.assignments.get_by_scope_ids(role_id, ids)
        selected = self.select_creates(
            data.items,
            [scope.id for scope in scopes],
            [row.scope_id for row in existing],
        )
        rows: Sequence[RoleScopeModel] = []
        if selected.items:
            rows = await self.assignments.create_batch(role_id, selected.items)
        result = self.batch_result(
            [item.scope_id for item in selected.items], rows, selected.errors
        )
        await self.audit.record_many(
            actor_id,
            [
                _event(AuditAction.ROLE_SCOPE_CREATE, row)
                for row in result.items
            ],
        )
        return result

    @transactional
    async def update_batch(
        self, role_id: int, data: RoleScopeBatchUpdate, *, actor_id: int
    ) -> BatchResultType[RoleScopeModel, ValidationException]:
        """Pre-read parent assignments and replace only matching masks in bulk.

        Args:
            role_id: Parent role checked once through its owning service.
            data: One to 100 scope/mask inputs; repeated writes are rejected.
            actor_id: Verified operator changing the masks.

        Returns:
            Updated records in input order and indexed errors for missing or
            repeated assignments. Other roles' assignments are never accepted.

        Raises:
            NotFoundException: The parent role does not exist.
        """
        await self.roles.get_by_id(role_id)
        ids = [item.scope_id for item in data.items]
        existing = await self.assignments.get_by_scope_ids(role_id, ids)
        selected = self.select_updates(
            data.items, [row.scope_id for row in existing]
        )
        rows: Sequence[RoleScopeModel] = []
        if selected.items:
            rows = await self.assignments.update_batch(role_id, selected.items)
        result = self.batch_result(
            [item.scope_id for item in selected.items], rows, selected.errors
        )
        await self.audit.record_many(
            actor_id,
            [
                _event(AuditAction.ROLE_SCOPE_UPDATE, row)
                for row in result.items
            ],
        )
        return result
