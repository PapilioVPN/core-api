"""Validated filters for the panel's audit history."""

from typing import Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType, ValueType
from papilio.types.enums import SortOrder
from pydantic import AwareDatetime, Field, model_validator

from src.apps.core.access.audit.domain.dtos.validators.range import check_range
from src.apps.core.access.audit.domain.enums.actions import AuditAction
from src.apps.core.access.audit.domain.enums.sorts import AuditSortBy


class AuditSearch(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    actor_id: list[IdType] | None = Field(
        default=None, min_length=1, max_length=100
    )
    action: list[AuditAction] | None = Field(
        default=None, min_length=1, max_length=100
    )
    since: AwareDatetime | None = None
    until: AwareDatetime | None = None
    sort_by: AuditSortBy = AuditSortBy.CREATED_AT
    sort_order: SortOrder = SortOrder.DESC

    @model_validator(mode="after")
    def check_range(self) -> Self:
        """Require the exclusive upper bound to follow the lower bound."""
        check_range(self.since, self.until)
        return self
