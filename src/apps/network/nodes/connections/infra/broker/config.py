"""Stable broker identity and periodic node connection schedule."""

from ...app.pipelines.probe import PROBE_INTERVAL_SECONDS


class BrokerConfig:
    probe_task = "network.nodes.check_connections.v1"

    probe_schedule = [
        {
            "schedule_id": "network-node-probe",
            "interval": PROBE_INTERVAL_SECONDS,
        },
    ]
