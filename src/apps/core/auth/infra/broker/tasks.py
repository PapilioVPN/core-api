"""Typed maintenance task for administrator sessions."""

from papilio_tasks.apps.schedulers import Task

cleanup = Task[[], int](name="core.auth.sessions.cleanup.v1")
