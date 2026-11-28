"""Validate the native wire limits of a route simulation."""

from ipaddress import IPv4Address, IPv6Address


def require_unscoped_ip(
    value: IPv4Address | IPv6Address,
) -> IPv4Address | IPv6Address:
    if isinstance(value, IPv6Address) and value.scope_id is not None:
        raise ValueError("A route simulation address cannot include a zone")
    return value


def require_attribute_budget(value: dict[str, str]) -> dict[str, str]:
    if (
        sum(
            len(k.encode("utf-8")) + len(v.encode("utf-8"))
            for k, v in value.items()
        )
        > 16 << 10
    ):
        raise ValueError("Route attributes exceed 16 KiB")
    return value
