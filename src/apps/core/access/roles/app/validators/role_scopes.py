"""Pure assignment selection policies using native batch checks and results."""

from collections.abc import Sequence

from papilio.errors.exceptions import ValidationException
from papilio.schemas.results import BatchResultType
from papilio.tools.checks import Checks

from src.apps.core.access.roles.domain.dtos.role_scopes import (
    RoleScopeCreate,
    RoleScopeUpdate,
)
from src.apps.core.access.roles.domain.models.records import RoleScopeModel


class RoleScopeChecks(Checks[RoleScopeModel]):
    entity = "RoleScope"

    def select_creates(
        self,
        items: Sequence[RoleScopeCreate],
        scope_ids: Sequence[int],
        assigned_ids: Sequence[int],
    ) -> BatchResultType[RoleScopeCreate, ValidationException]:
        """Select new assignments and report rejected items.

        Args:
            items: At most 100 validated scope/mask inputs in request order.
            scope_ids: Authoritative existing scope identities.
            assigned_ids: Scopes already assigned to the parent role.

        Returns:
            Accepted first occurrences and indexed native per-item errors.
            No accepted items is a normal result, including all-invalid input.
        """
        missing = self._check_batch_data(
            scope_ids, [item.scope_id for item in items], ["items"]
        )
        errors = {error.loc[-1]: error for error in missing}
        assigned = set(assigned_ids)
        seen: set[int] = set()
        accepted: list[RoleScopeCreate] = []
        for index, item in enumerate(items):
            if item.scope_id in seen or item.scope_id in assigned:
                errors[index] = ValidationException(
                    message="Scope is repeated or already assigned",
                    message_code="duplicate_scope",
                    loc=["items", index],
                    input=item.scope_id,
                )
            if index not in errors:
                accepted.append(item)
            seen.add(item.scope_id)
        return BatchResultType(
            items=accepted, errors=[errors[i] for i in sorted(errors)]
        )

    def select_updates(
        self, items: Sequence[RoleScopeUpdate], assigned_ids: Sequence[int]
    ) -> BatchResultType[RoleScopeUpdate, ValidationException]:
        """Select assigned scopes for update, preserving each first occurrence.

        Args:
            items: At most 100 validated scope/mask inputs in request order.
            assigned_ids: Authoritative scope identities assigned to this role.

        Returns:
            Accepted items and indexed missing-assignment or duplicate errors.
            All-invalid input returns no items without raising an exception.
        """
        missing = self._check_batch_data(
            assigned_ids, [item.scope_id for item in items], ["items"]
        )
        errors = {error.loc[-1]: error for error in missing}
        seen: set[int] = set()
        accepted: list[RoleScopeUpdate] = []
        for index, item in enumerate(items):
            if item.scope_id in seen:
                errors[index] = ValidationException(
                    message="Scope is repeated within this batch",
                    message_code="duplicate_scope",
                    loc=["items", index],
                    input=item.scope_id,
                )
            if index not in errors:
                accepted.append(item)
            seen.add(item.scope_id)
        return BatchResultType(
            items=accepted, errors=[errors[i] for i in sorted(errors)]
        )

    def batch_result(
        self,
        scope_ids: Sequence[int],
        rows: Sequence[RoleScopeModel],
        errors: Sequence[ValidationException],
    ) -> BatchResultType[RoleScopeModel, ValidationException]:
        """Order actual written records and retain selection errors.

        Args:
            scope_ids: Accepted scope identities in input order; may be empty.
            rows: Actual records returned by the native bulk mutation.
            errors: Indexed errors from pre-write selection.

        Returns:
            Materialized records in accepted order, their row IDs and errors.

        Raises:
            ValidationException: A mutation omitted accepted rows.
        """
        missing = self._check_batch_data(
            [row.scope_id for row in rows], scope_ids, ["items"]
        )
        if missing:
            raise ValidationException.get_invalid_input(missing)
        by_scope = {row.scope_id: row for row in rows}
        return BatchResultType(
            items=[by_scope[id] for id in scope_ids],
            errors=errors,
            item_ids={row.id for row in rows},
        )
