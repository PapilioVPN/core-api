"""Inputs to save or browse immutable Xray configuration revisions."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType
from pydantic import field_validator

from .validation import XrayConfigCandidate
from .validators.revisions import require_json_object


class XrayRevisionCreate(XrayConfigCandidate):
    @field_validator("config_json")
    @classmethod
    def require_json(cls, value: bytes) -> bytes:
        return require_json_object(value)


class XrayRevisionList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
