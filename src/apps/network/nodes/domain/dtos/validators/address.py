"""Validate an address without resolving or contacting the node."""

import re
from ipaddress import ip_address

from pydantic_core import PydanticCustomError

_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)


def normalize_address(value: str) -> str:
    """Normalize an unbracketed IP address or ASCII DNS hostname.

    Args:
        value: Management address without transport, port or zone identifier.

    Returns:
        Canonical IP literal or a lowercase DNS hostname without the root dot.

    Raises:
        PydanticCustomError: The value is not a supported address.
    """
    try:
        if "%" in value:
            raise ValueError("Scoped addresses are not supported")
        address = str(ip_address(value))
    except ValueError:
        address = value.removesuffix(".").lower()
        labels = address.split(".")
        if (
            len(address) > 253
            or not value.isascii()
            or labels[-1].isdigit()
            or not all(_LABEL.fullmatch(label) for label in labels)
        ):
            raise PydanticCustomError(
                "node_address",
                "Enter a DNS name or IP address without a scheme or port",
            ) from None
    return address
