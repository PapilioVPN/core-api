"""Physical sensor readings in Celsius, RPM and seconds."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class Temperature:
    device: str
    label: str
    current_celsius: float
    high_celsius: float | None
    critical_celsius: float | None


@dataclass(frozen=True, slots=True)
class FanSpeed:
    device: str
    label: str
    rpm: int


@dataclass(frozen=True, slots=True)
class BatteryInfo:
    observed_at: datetime
    percent: float
    plugged_in: bool
    remaining_seconds: int | None
    remaining_time: Literal["known", "unknown", "unlimited"]
