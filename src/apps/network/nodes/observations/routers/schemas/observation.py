"""Common Node target and delivery information for engine observations."""

from datetime import datetime
from typing import Annotated

from papilio.schemas.outputs import BaseOutput
from pydantic import Field

from ...domain.enums.observation import NodeReadStatus

# Preserve uint64 precision in JavaScript, including values above 2**53.
type UInt64Text = Annotated[str, Field(coerce_numbers_to_str=True)]


class NodeObservationOutput(BaseOutput):
    node_id: int
    status: NodeReadStatus
    received_at: datetime | None
