"""Typed rate refresh task shared by the worker and schedule."""

from papilio_tasks.apps.schedulers import Task

from .config import BrokerConfig

refresh_rate = Task[[], None](name=BrokerConfig.refresh_task)
