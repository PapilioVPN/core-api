"""Lifecycle and halt reasons of an ordered Xray restart plan."""

from enum import StrEnum


class RestartRolloutState(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    HALTED = "halted"


class RestartRolloutReason(StrEnum):
    ACTIVE_OPERATION = "active_operation"
    TARGET_FAILED = "target_failed"
    TARGET_UNKNOWN = "target_unknown"
    DIGEST_MISMATCH = "digest_mismatch"
