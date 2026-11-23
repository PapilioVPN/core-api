"""Variant-style metadata for audit history search."""

from typing import Annotated, Literal

from papilio.api.responses.meta import FilterMeta, PagerMeta, SortMeta
from papilio.schemas.outputs import BaseOutput
from papilio.types.enums import FilterType
from pydantic import Field

from src.apps.core.audit.domain.enums.actions import AuditAction


class OptionOutput(BaseOutput):
    id: int | AuditAction
    label: str
    count: int


class TermOutput(FilterMeta[OptionOutput]):
    key: Literal["actor_id", "action"]
    id: int | None = Field(default=None, exclude=True)
    type: FilterType = FilterType.CHECKBOX


class TimeOutput(BaseOutput):
    key: Literal["created_at"] = "created_at"
    title: str = "زمان ثبت"
    type: Literal[FilterType.SLIDER] = FilterType.SLIDER
    minimum: float | None
    maximum: float | None


type FilterOutput = Annotated[
    TermOutput | TimeOutput, Field(discriminator="key")
]


class AuditMeta(BaseOutput):
    pager: PagerMeta
    filters: list[FilterOutput]
    sorts: SortMeta
