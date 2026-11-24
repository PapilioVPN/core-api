"""Read optional hardware sensors without substituting missing measurements."""

from datetime import UTC, datetime

import psutil

from src.apps.core.system.info.domain.results.sensors import (
    BatteryInfo,
    FanSpeed,
    Temperature,
)


class SensorReader:
    def read_temperatures(self) -> tuple[Temperature, ...] | None:
        """Read native temperature sensors in degrees Celsius.

        Args:
            None.

        Returns:
            Readings ordered by device name; None on unsupported platforms
            and an empty tuple when supported but no readings are present.
        """
        result: tuple[Temperature, ...] | None = None
        if psutil.LINUX or psutil.FREEBSD:
            readings = psutil.sensors_temperatures()
            result = tuple(
                Temperature(
                    device=device,
                    label=item.label,
                    current_celsius=item.current,
                    high_celsius=item.high,
                    critical_celsius=item.critical,
                )
                for device in sorted(readings)
                for item in readings[device]
            )
        return result

    def read_fans(self) -> tuple[FanSpeed, ...] | None:
        """Read native fan speed sensors in revolutions per minute.

        Args:
            None.

        Returns:
            Readings ordered by device name; None on unsupported platforms
            and an empty tuple when supported but no readings are present.
        """
        result: tuple[FanSpeed, ...] | None = None
        if psutil.LINUX:
            readings = psutil.sensors_fans()
            result = tuple(
                FanSpeed(device=device, label=item.label, rpm=item.current)
                for device in sorted(readings)
                for item in readings[device]
            )
        return result

    def read_battery(self) -> BatteryInfo | None:
        """Read native battery charge and remaining-time information.

        Args:
            None.

        Returns:
            Battery information, or None when absent or unsupported.
            Unknown or unlimited remaining time has remaining_seconds=None.
        """
        battery = (
            psutil.sensors_battery()
            if psutil.LINUX or psutil.WINDOWS or psutil.FREEBSD or psutil.MACOS
            else None
        )
        result: BatteryInfo | None = None
        if battery is not None:
            remaining = battery.secsleft
            result = BatteryInfo(
                observed_at=datetime.now(UTC),
                percent=battery.percent,
                plugged_in=battery.power_plugged,
                remaining_seconds=remaining if remaining >= 0 else None,
                remaining_time=(
                    "unlimited"
                    if remaining == psutil.POWER_TIME_UNLIMITED
                    else "known"
                    if remaining >= 0
                    else "unknown"
                ),
            )
        return result
