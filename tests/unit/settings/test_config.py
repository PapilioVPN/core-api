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
