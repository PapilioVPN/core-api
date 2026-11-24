"""Physical sensor readings in Celsius, RPM and seconds."""

from datetime import datetime
from typing import Literal

from papilio.schemas.outputs import BaseOutput


class TemperatureOutput(BaseOutput):
    device: str
    label: str
    current_celsius: float
    high_celsius: float | None
    critical_celsius: float | None


class FanOutput(BaseOutput):
    device: str
    label: str
    rpm: int


class BatteryOutput(BaseOutput):
    observed_at: datetime
    percent: float
    plugged_in: bool
    remaining_seconds: int | None
    remaining_time: Literal["known", "unknown", "unlimited"]
