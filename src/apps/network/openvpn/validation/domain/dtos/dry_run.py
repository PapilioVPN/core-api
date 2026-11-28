"""Bound the proposed OpenVPN source to the Node v1 limit."""

from papilio.schemas.inputs import BaseDTO
from pydantic import Field


class OpenVPNCandidate(BaseDTO):
    config_text: bytes = Field(min_length=1, max_length=1 << 20, repr=False)
