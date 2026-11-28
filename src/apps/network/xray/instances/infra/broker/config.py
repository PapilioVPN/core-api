"""Stable identities for committed Xray execution requests."""

from faststream.nats import JStream


class BrokerConfig:
    start_requested = "papiliovpn.network.xray.start.requested.v1"
    start_durable = "papiliovpn_network_xray_start"
    stream = JStream("papiliovpn_network_xray", subjects=[start_requested])
    apply_requested = "papiliovpn.network.xray.apply.requested.v1"
    apply_durable = "papiliovpn_network_xray_apply"
    apply_stream = JStream(
        "papiliovpn_network_xray_apply", subjects=[apply_requested]
    )
    control_requested = "papiliovpn.network.xray.control.requested.v1"
    control_durable = "papiliovpn_network_xray_control"
    control_stream = JStream(
        "papiliovpn_network_xray_control", subjects=[control_requested]
    )
    rollout_requested = "papiliovpn.network.xray.restart_rollout.requested.v1"
    rollout_durable = "papiliovpn_network_xray_restart_rollout"
    rollout_stream = JStream(
        "papiliovpn_network_xray_restart_rollout", subjects=[rollout_requested]
    )
