"""Declare the typed IPG reconciliation task."""

from papilio_tasks.apps.schedulers import Task

from ...domain.dtos.verify import VerifyPolicy
from ...domain.results.verify import VerifyBatch
from .config import BrokerConfig

verify_payments = Task[[VerifyPolicy], VerifyBatch](
    name=BrokerConfig.verify_task
)
