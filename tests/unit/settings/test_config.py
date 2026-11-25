"""Validate configured Core, job and CLI options at the settings boundary."""

import pytest
from pydantic import ValidationError

from src.settings.cli import CLIConfig
from src.settings.config import NatsConfig, SchedulerConfig

pytestmark = pytest.mark.unit


def test_settings_reject_unknown_keys() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        NatsConfig.model_validate({"servers": ["nats://localhost"], "typo": 1})
    with pytest.raises(ValidationError, match="extra_forbidden"):
        SchedulerConfig.model_validate({"typo": "jobs"})
    with pytest.raises(ValidationError, match="extra_forbidden"):
        CLIConfig.model_validate({"theme": {"typo": "red"}})


def test_scheduler_rejects_empty_transport_values() -> None:
    with pytest.raises(ValidationError, match="string_too_short"):
        SchedulerConfig(stream="")


def test_rate_schedule_is_opt_in_and_uses_whole_seconds() -> None:
    assert SchedulerConfig().rate_refresh_interval is None
    assert (
        SchedulerConfig(rate_refresh_interval=45).rate_refresh_interval == 45
    )
    with pytest.raises(ValidationError):
        SchedulerConfig(rate_refresh_interval=0)
    with pytest.raises(ValidationError):
        SchedulerConfig.model_validate({"rate_refresh_interval": 1.5})
