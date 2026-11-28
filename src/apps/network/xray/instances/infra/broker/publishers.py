"""Publish committed Xray execution requests through the native Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.apply import XrayApplyRequested
from ...domain.events.control import XrayControlRequested
from ...domain.events.rollout import XrayRestartRolloutRequested
from ...domain.events.start import XrayStartRequested
from .config import BrokerConfig

start_requested = publisher(
    XrayStartRequested,
    subject=BrokerConfig.start_requested,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.start_requested,
)

apply_requested = publisher(
    XrayApplyRequested,
    subject=BrokerConfig.apply_requested,
    stream=BrokerConfig.apply_stream,
    outbox_key=BrokerConfig.apply_requested,
)

control_requested = publisher(
    XrayControlRequested,
    subject=BrokerConfig.control_requested,
    stream=BrokerConfig.control_stream,
    outbox_key=BrokerConfig.control_requested,
)

rollout_requested = publisher(
    XrayRestartRolloutRequested,
    subject=BrokerConfig.rollout_requested,
    stream=BrokerConfig.rollout_stream,
    outbox_key=BrokerConfig.rollout_requested,
)
