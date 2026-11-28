"""Materialized progress and the worker's next delivery decision."""

from dataclasses import dataclass

from ..enums.rollout import RestartRolloutDelivery
from ..models.rollout import (
    XrayRestartRolloutModel,
    XrayRestartRolloutTargetModel,
)
from ..models.start import XrayStartModel


@dataclass(frozen=True, slots=True)
class RestartRolloutStep:
    target: XrayRestartRolloutTargetModel
    operation: XrayStartModel | None


@dataclass(frozen=True, slots=True)
class RestartRolloutSnapshot:
    rollout: XrayRestartRolloutModel
    steps: tuple[RestartRolloutStep, ...]

    @property
    def id(self) -> int:
        """Identify this snapshot by its persisted plan."""
        return self.rollout.id


@dataclass(frozen=True, slots=True)
class RetryRestartRolloutDelivery:
    seconds: float


type RestartRolloutDecision = (
    RestartRolloutDelivery | RetryRestartRolloutDelivery
)
