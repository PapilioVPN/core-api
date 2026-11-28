"""Materialized progress and the worker's next delivery decision."""

from dataclasses import dataclass

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
class RestartRolloutDecision:
    dispatch: bool = False
    retry_after: float | None = None
