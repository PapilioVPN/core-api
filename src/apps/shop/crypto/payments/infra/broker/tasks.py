"""Typed crypto payment maintenance task."""

from papilio_tasks.apps.schedulers import Task

from ...domain.dtos.recheck import PaymentRecheck

recheck_payments = Task[[PaymentRecheck], int](
    name="shop.crypto.payments.recheck.v1"
)
