"""Inputs to save or browse immutable Xray configuration revisions."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType
from pydantic import field_validator

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
