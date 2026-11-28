"""Inputs to save or browse immutable Xray configuration revisions."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType
from pydantic import AfterValidator, Field, field_validator

from src.shared.utils.order import require_distinct_ids

from .source import XrayConfigCandidate
from .validators.source import require_json_object


class XrayRevisionCreate(XrayConfigCandidate):
    @field_validator("config_json")
    @classmethod
    def require_json(cls, value: bytes) -> bytes:
        return require_json_object(value)


class XrayRevisionList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20


class XrayRevisionSelectionInput(BaseDTO):
    before_id: IdType | None = None
    per_page: PerPageType = 20


class XrayRevisionBulkRemoveInput(BaseDTO):
    ids: list[Annotated[IdType, Field(strict=True)]] = Field(
        min_length=1, max_length=100
    )


class XrayRevisionOrderInput(BaseDTO):
    ordered_ids: Annotated[
        list[Annotated[IdType, Field(strict=True)]],
        Field(min_length=2, max_length=10_000),
        AfterValidator(require_distinct_ids),
    ]
