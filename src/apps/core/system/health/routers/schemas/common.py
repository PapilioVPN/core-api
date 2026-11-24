"""Explicit HTTP schemas; Papilio owns normal response encoding."""

from datetime import datetime as DateTime

from papilio.schemas.outputs import BaseOutput


class MeasurementOutput[T](BaseOutput):
    value: T
    duration_ms: float


class ProbeOutput(BaseOutput):
    status: str
    value: bool
    duration_ms: float


class ServerTimeOutput(BaseOutput):
    datetime: DateTime
    timezone: str


class PublicHealthOutput(BaseOutput):
    status: str
    server_time: ServerTimeOutput | None
    duration_ms: float


class PostgresClockOutput(BaseOutput):
    server_time: DateTime
    server_timezone: str


class PostgresHealthOutput(BaseOutput):
    status: str
    value: PostgresClockOutput | None
    duration_ms: float
