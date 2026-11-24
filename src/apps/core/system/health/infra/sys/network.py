"""Read interface metadata and native aggregate/per-interface counters."""

from datetime import UTC, datetime

import psutil

from src.apps.core.system.health.domain.results.network import (
    InterfaceAddress,
    InterfaceStatus,
    NetworkInterface,
    NetworkIoCounters,
)


class NetworkReader:
    def read_interfaces(self) -> tuple[NetworkInterface, ...]:
        """Read native interface addresses and status.

        Args:
            None.

        Returns:
            Interfaces ordered by name; unavailable status remains None.
        """
        addresses = psutil.net_if_addrs()
        statuses = psutil.net_if_stats()
        interfaces: list[NetworkInterface] = []
        for name in sorted(addresses.keys() | statuses.keys()):
            status = statuses.get(name)
            interfaces.append(
                NetworkInterface(
                    name=name,
                    addresses=tuple(
                        InterfaceAddress(
                            family=int(item.family),
                            address=item.address,
                            netmask=item.netmask,
                            broadcast=item.broadcast,
                            point_to_point=item.ptp,
                        )
                        for item in addresses.get(name, ())
                    ),
                    status=(
                        InterfaceStatus(
                            is_up=status.isup,
                            duplex=int(status.duplex),
                            speed_mbps=status.speed,
                            mtu_bytes=status.mtu,
                            flags=status.flags,
                        )
                        if status is not None
                        else None
                    ),
                )
            )
        return tuple(interfaces)

    def read_io_counters(self) -> tuple[NetworkIoCounters, ...] | None:
        """Read cumulative network I/O counters for each interface.

        Args:
            None.

        Returns:
            Counters ordered by interface name, or None if unavailable.
            Byte fields are bytes; packet, error and drop fields are counts.
        """
        counters = psutil.net_io_counters(pernic=True)
        result: tuple[NetworkIoCounters, ...] | None = None
        if counters is not None:
            observed_at = datetime.now(UTC)
            result = tuple(
                NetworkIoCounters(
                    observed_at=observed_at,
                    interface=name,
                    bytes_sent=counters[name].bytes_sent,
                    bytes_received=counters[name].bytes_recv,
                    packets_sent=counters[name].packets_sent,
                    packets_received=counters[name].packets_recv,
                    errors_in=counters[name].errin,
                    errors_out=counters[name].errout,
                    dropped_in=counters[name].dropin,
                    dropped_out=counters[name].dropout,
                )
                for name in sorted(counters)
            )
        return result

    def read_total_io_counters(self) -> NetworkIoCounters | None:
        """Read native cumulative network I/O totals.

        Args:
            None.

        Returns:
            Aggregate byte and packet counters with interface=None, or None
            if the native tool cannot provide counters.
        """
        counters = psutil.net_io_counters()
        result: NetworkIoCounters | None = None
        if counters is not None:
            result = NetworkIoCounters(
                observed_at=datetime.now(UTC),
                interface=None,
                bytes_sent=counters.bytes_sent,
                bytes_received=counters.bytes_recv,
                packets_sent=counters.packets_sent,
                packets_received=counters.packets_recv,
                errors_in=counters.errin,
                errors_out=counters.errout,
                dropped_in=counters.dropin,
                dropped_out=counters.dropout,
            )
        return result
