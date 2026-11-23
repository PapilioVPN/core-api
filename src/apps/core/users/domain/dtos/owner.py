"""Credentials and names for local first-owner setup."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MobileType, MStrType, PasswordType
from pydantic import Field


class OwnerCreate(BaseDTO):
    first_name: MStrType
    last_name: MStrType
    mobile: MobileType
    password: PasswordType = Field(repr=False)
