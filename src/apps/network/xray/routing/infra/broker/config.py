"""Own native JetStream identities for Xray routing operations."""

from faststream.nats import JStream


class BrokerConfig:
    requested = "papiliovpn.network.xray.routing.requested.v1"
    durable = "papiliovpn_network_xray_routing"
    stream = JStream("papiliovpn_network_xray_routing", subjects=[requested])
