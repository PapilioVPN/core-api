"""Operator selections for the three native reset actions."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from pydantic import AfterValidator, BeforeValidator, Field

from ..enums.reset import TrafficDirection
from .traffic import XrayCounterName


def _confirm(value: object) -> bool:
    if value is not True:
        raise ValueError("Scope reset requires explicit confirmation")
    return True


def _stored_name(value: str) -> str:
    if "\x00" in value:
        raise ValueError("The counter name cannot contain a NUL byte")
    return value


type ResetCounterName = Annotated[
    XrayCounterName, AfterValidator(_stored_name)
]


class PairResetInput(BaseDTO):
    name: ResetCounterName


class CounterResetInput(BaseDTO):
    name: ResetCounterName
    direction: TrafficDirection


class ScopeResetInput(BaseDTO):
    max_counters: Annotated[int, Field(strict=True, ge=1, le=1000)]
    confirm: Annotated[bool, BeforeValidator(_confirm)]
