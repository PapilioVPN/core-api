"""Untrusted input for administrator password login."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MobileType, PasswordType
from pydantic import Field


class PasswordLogin(BaseDTO):
    """Credentials only; audience and claims belong to the account owner."""

    mobile: MobileType
    password: PasswordType = Field(repr=False)
