"""Typed recheck task used by the native worker and scheduler."""

from papilio_tasks.apps.schedulers import Task

from ...domain.dtos.recheck import PaymentRecheck
from ...domain.results.check import RecheckStats

recheck_payments = Task[[PaymentRecheck], RecheckStats](
    name="shop.crypto.payments.recheck.v1"
)
