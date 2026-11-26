"""Inputs for a dry run of proposed Xray JSON on a registered node."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from pydantic import Field, StringConstraints, field_validator
from pydantic_core import PydanticCustomError

type XrayInstanceID = Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
]

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
