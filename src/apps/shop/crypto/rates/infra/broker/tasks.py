"""Typed rate refresh task shared by the worker and schedule."""

from papilio_tasks.apps.schedulers import Task

from ...domain.models.records import Rate
from ...domain.results.records import RateFailure
from .config import BrokerConfig

refresh_rate = Task[[], Rate | RateFailure](name=BrokerConfig.refresh_task)
