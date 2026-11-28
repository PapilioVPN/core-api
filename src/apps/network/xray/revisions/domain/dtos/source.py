"""Exact source bytes accepted by Xray revision creation and dry runs."""

from papilio.schemas.inputs import BaseDTO
from pydantic import Field, field_validator
from pydantic_core import PydanticCustomError

# Node's runconfig.MaxSourceBytes in the pinned v1 contract.
_MAX_SOURCE_BYTES = 1 << 20


class XrayConfigCandidate(BaseDTO):
    config_json: bytes = Field(
        min_length=1, max_length=_MAX_SOURCE_BYTES, repr=False
    )

    @field_validator("config_json")
    @classmethod
    def require_source(cls, value: bytes) -> bytes:
        """Require a proposal and preserve its exact bytes."""
        if not value.strip():
            raise PydanticCustomError(
                "xray_config_empty", "A proposed Xray config is required"
            )
        return value
