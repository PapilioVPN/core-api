"""JWT claims validated at the codec boundary."""

from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID

from pydantic import Field, JsonValue, StrictInt, StrictStr, TypeAdapter


@dataclass(frozen=True, slots=True)
class Payload:
    sub: Annotated[StrictStr, Field(min_length=1)]
    aud: Annotated[StrictStr, Field(min_length=1)]
    jti: Annotated[StrictStr, Field(min_length=1)]
    iat: Annotated[StrictInt, Field(ge=0)]
    exp: Annotated[StrictInt, Field(gt=0)]
    sid: UUID | None = None
    data: dict[str, JsonValue] = field(default_factory=dict, repr=False)


PAYLOAD = TypeAdapter(Payload)
