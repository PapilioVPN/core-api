"""Input for a password change on the authenticated account."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PasswordType
from pydantic import Field


class UserPasswordUpdate(BaseDTO):
    current_password: PasswordType = Field(repr=False)
    password: PasswordType = Field(repr=False)
