"""Ordered, bounded target selection for a rolling restart."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType
from pydantic import AfterValidator, Field

from .identity import XrayInstanceID


class RestartRolloutTarget(BaseDTO):
    node_id: Annotated[IdType, Field(strict=True)]
    instance_id: XrayInstanceID


def _distinct(
    targets: list[RestartRolloutTarget],
) -> list[RestartRolloutTarget]:
    if len({(row.node_id, row.instance_id) for row in targets}) != len(
        targets
    ):
        raise ValueError("A rollout target may appear only once")
    return targets


class RestartRolloutInput(BaseDTO):
    targets: Annotated[
        list[RestartRolloutTarget],
        Field(min_length=1, max_length=16),
        AfterValidator(_distinct),
    ]
