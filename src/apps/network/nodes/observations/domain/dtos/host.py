"""Bound the Panel's explicit live host selection."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType
from pydantic import Field


class FleetHostStatsInput(BaseDTO):
    node_ids: list[Annotated[IdType, Field(strict=True)]] = Field(
        min_length=1, max_length=16
    )
