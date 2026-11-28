"""Own native JetStream identities for Xray traffic reset operations."""

from faststream.nats import JStream


class BrokerConfig:
    requested = "papiliovpn.network.xray.traffic_reset.requested.v1"
    durable = "papiliovpn_network_xray_traffic_reset"
    stream = JStream(
        "papiliovpn_network_xray_traffic_reset", subjects=[requested]
    )
