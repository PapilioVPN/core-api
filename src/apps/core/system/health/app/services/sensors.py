"""Measured system reads through native worker threads."""

from anyio import to_thread

from src.apps.core.system.health.app.helpers.measurement import measure
from src.apps.core.system.health.domain.results.sensors import (
    BatteryInfo,
    FanSpeed,
    Temperature,
)
from src.apps.core.system.health.domain.results.services import (
    MeasuredResult,
)
from src.apps.core.system.health.infra.sys.sensors import SensorReader


class SensorHealthService:
    def __init__(self, reader: SensorReader) -> None:
        """Bind the focused reader and native thread execution.

        Args:
            reader: Synchronous system reader.


        Returns:
            None.
        """
        self.reader = reader

    async def read_temperatures(
        self,
    ) -> MeasuredResult[tuple[Temperature, ...] | None]:
        """Read supported temperature sensors without blocking the loop.

        Args:
            None.

        Returns:
            Celsius readings in device-name/native reading order, or None on
            unsupported platforms, with elapsed milliseconds. A supported
            platform without readings yields an empty tuple.
        """
        result = await measure(
            to_thread.run_sync, self.reader.read_temperatures
        )
        return result

    async def read_fans(
        self,
    ) -> MeasuredResult[tuple[FanSpeed, ...] | None]:
        """Read supported fan speed sensors without blocking the loop.

        Args:
            None.

        Returns:
            RPM readings in device-name/native reading order, or None on
            unsupported platforms, with elapsed milliseconds. A supported
            platform without readings yields an empty tuple.
        """
        result = await measure(to_thread.run_sync, self.reader.read_fans)
        return result

    async def read_battery(self) -> MeasuredResult[BatteryInfo | None]:
        """Read battery status without blocking the event loop.

        Args:
            None.

        Returns:
            Battery metadata, or None if absent/unsupported, and elapsed
            milliseconds. Unknown/unlimited remaining seconds stay None.
        """
        result = await measure(to_thread.run_sync, self.reader.read_battery)
        return result
