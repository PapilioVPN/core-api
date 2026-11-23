"""Typed maintenance task for administrator sessions."""

from papilio_tasks.apps.schedulers import Task

cleanup_sessions = Task[[], int](name="core.auth.sessions.cleanup.v1")
