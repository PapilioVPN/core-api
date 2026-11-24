"""HTTP schema for results with elapsed time."""

from papilio.schemas.outputs import BaseOutput


class MeasurementOutput[T](BaseOutput):
    value: T
    duration_ms: float
