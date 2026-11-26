"""Stable identities for committed Xray start requests."""

from faststream.nats import JStream


class BrokerConfig:
    start_requested = "papiliovpn.network.xray.start.requested.v1"
    start_durable = "papiliovpn_network_xray_start"
    stream = JStream("papiliovpn_network_xray", subjects=[start_requested])
