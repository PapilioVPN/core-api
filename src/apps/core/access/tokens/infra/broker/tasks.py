"""Typed refresh history maintenance task."""

from papilio_tasks.apps.schedulers import Task

from src.apps.core.access.tokens.domain.dtos.refresh import RefreshUseCleanup

cleanup_refresh = Task[[RefreshUseCleanup], int](name="core.tokens.cleanup.v1")
