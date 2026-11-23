"""Untrusted refresh credential for administrator renewal or logout."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import ContentType
from pydantic import Field


class TokenRefresh(BaseDTO):
    """Carry the credential; the token owner verifies JWT authenticity."""

    refresh_token: ContentType = Field(min_length=1, repr=False)
