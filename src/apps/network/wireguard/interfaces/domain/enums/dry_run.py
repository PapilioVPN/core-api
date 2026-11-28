"""Stable WireGuard candidate validation outcomes."""

from enum import StrEnum


class WireGuardIssue(StrEnum):
    UNKNOWN = "unknown"
    INVALID_JSON = "invalid_json"
    INVALID_PRIVATE_KEY = "invalid_private_key"
    INVALID_ADDRESSES = "invalid_addresses"
    DUPLICATE_ADDRESS = "duplicate_address"
    INVALID_MTU = "invalid_mtu"
    INVALID_LISTEN_PORT = "invalid_listen_port"
    INVALID_INITIAL_PEERS = "invalid_initial_peers"
