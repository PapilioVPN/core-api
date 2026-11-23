"""Validated JWT wire payload, separate from trusted identity records."""

from papilio.security.tokens import TokenType
from pydantic import BaseModel, Field, JsonValue, StrictInt, StrictStr


class JWTPayload(BaseModel):
    sub: StrictStr = Field(min_length=1)
    aud: StrictStr = Field(min_length=1)
    type: TokenType
    jti: StrictStr = Field(min_length=1)
    iat: StrictInt = Field(ge=0)
    exp: StrictInt = Field(gt=0)
    data: dict[str, JsonValue] = Field(default_factory=dict, repr=False)
