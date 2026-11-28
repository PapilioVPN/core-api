"""Explicit operator selections and tracking keys for fleet Apply."""

from functools import partial
from typing import Annotated
from uuid import UUID

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType
from pydantic import AfterValidator, Field

from .identity import XrayInstanceTarget
from .validators.fleet import require_distinct_targets


class XrayFleetApplyTarget(XrayInstanceTarget):
    request_key: UUID


class XrayFleetApplyInput(BaseDTO):
    targets: Annotated[
        list[XrayFleetApplyTarget],
        Field(min_length=1, max_length=16),
        AfterValidator(
            partial(require_distinct_targets, selection="an Apply selection")
        ),
    ]


class XrayFleetApplyTrackingTarget(XrayInstanceTarget):
    operation_id: Annotated[IdType, Field(strict=True)]


class XrayFleetApplyTrackingInput(BaseDTO):
    targets: list[XrayFleetApplyTrackingTarget] = Field(
        min_length=1, max_length=16
    )
