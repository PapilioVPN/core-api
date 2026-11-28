"""Typed connection check entrypoint for the scheduler and worker."""

from papilio_tasks.apps.schedulers import Task

from ...domain.results.probe import NodeProbeBatch
from .config import BrokerConfig

check_connections = Task[[], NodeProbeBatch](name=BrokerConfig.probe_task)
