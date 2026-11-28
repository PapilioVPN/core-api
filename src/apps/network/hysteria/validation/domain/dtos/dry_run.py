"""Bound the proposed Hysteria source to the Node v1 limit."""

from papilio.schemas.inputs import BaseDTO
from pydantic import Field


class HysteriaCandidate(BaseDTO):
    config_yaml: bytes = Field(min_length=1, max_length=1 << 20, repr=False)
