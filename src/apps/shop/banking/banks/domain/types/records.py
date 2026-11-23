"""Stable Iranian bank codes."""

from typing import Annotated

from papilio.types.aliases import ValueType
from pydantic import Field

BankCodeType = Annotated[ValueType, Field(max_length=32)]
