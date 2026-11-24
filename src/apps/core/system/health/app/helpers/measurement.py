"""Measure awaited health operations with Python's monotonic clock."""

from collections.abc import Awaitable, Callable
from time import perf_counter_ns

from src.apps.core.system.health.domain.results.services import MeasuredResult


async def measure[**P, T](
    operation: Callable[P, Awaitable[T]], /, *args: P.args, **kwargs: P.kwargs
) -> MeasuredResult[T]:
    """Measure an async operation until its typed value is ready.

    Args:
        operation: Async callable; blocking work must already use a worker.
        *args: Positional arguments passed unchanged.
        **kwargs: Keyword arguments passed unchanged.

    Returns:
        Original value with elapsed milliseconds, including worker waiting.
        Operation errors and cancellation propagate without a result.
    """
    started = perf_counter_ns()
    value = await operation(*args, **kwargs)
    duration_ms = (perf_counter_ns() - started) / 1_000_000
    return MeasuredResult(value=value, duration_ms=duration_ms)
