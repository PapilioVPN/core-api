"""Editable self-profile fields, separate from verified contact changes."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MStrType
from pydantic_core import MISSING


class UserProfileUpdate(BaseDTO):
    """Patch names only; authenticated identity is supplied separately."""

    first_name: MStrType | MISSING = MISSING
    last_name: MStrType | MISSING = MISSING
