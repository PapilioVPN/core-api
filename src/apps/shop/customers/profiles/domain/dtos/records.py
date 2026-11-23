"""Validated customer profile writes from the panel."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MobileType, MStrType
from pydantic import Field
from pydantic_core import MISSING

NoteType = Annotated[str, Field(max_length=500)]


class ProfileCreate(BaseDTO):
    name: MStrType
    mobile: MobileType | None = None
    note: NoteType | None = None
    is_blocked: bool = False


class ProfileUpdate(BaseDTO):
    name: MStrType | MISSING = MISSING
    mobile: MobileType | None = None
    note: NoteType | None = None
    is_blocked: bool | MISSING = MISSING
