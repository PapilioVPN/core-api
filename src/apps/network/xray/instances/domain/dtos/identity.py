"""Identities shared by Xray instance operations."""

from typing import Annotated
from uuid import UUID

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType
from pydantic import Field, StringConstraints

type XrayInstanceID = Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
]


type XrayExecutionKey = tuple[int, str]
type XrayExecutionRequestKey = tuple[int, str, UUID]
type XrayExecutionTrackingKey = tuple[int, str, int]


class XrayInstanceTarget(BaseDTO):
    node_id: Annotated[IdType, Field(strict=True)]
    instance_id: XrayInstanceID


type XrayInstanceTargets = Annotated[
    list[XrayInstanceTarget], Field(min_length=1, max_length=16)
]
