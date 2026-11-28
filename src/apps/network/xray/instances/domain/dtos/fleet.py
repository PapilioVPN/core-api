"""Explicit bounded selections for local Start and Stop."""

from functools import partial
from typing import Annotated
from uuid import UUID

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType
from pydantic import AfterValidator, Field

from .identity import XrayInstanceTarget
from .validators.fleet import require_distinct_targets


class XrayFleetRequestTarget(XrayInstanceTarget):
    request_key: UUID


class XrayFleetStartInput(BaseDTO):
    targets: Annotated[
        list[XrayFleetRequestTarget],
        Field(min_length=1, max_length=16),
        AfterValidator(
            partial(require_distinct_targets, selection="a Start selection")
        ),
    ]


class XrayFleetStopInput(BaseDTO):
    targets: Annotated[
        list[XrayFleetRequestTarget],
        Field(min_length=1, max_length=16),
        AfterValidator(
            partial(require_distinct_targets, selection="a Stop selection")
        ),
    ]


class XrayFleetTrackingTarget(XrayInstanceTarget):
    operation_id: Annotated[IdType, Field(strict=True)]


class XrayFleetTrackingInput(BaseDTO):
    targets: list[XrayFleetTrackingTarget] = Field(min_length=1, max_length=16)
