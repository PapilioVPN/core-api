"""Check one due batch with bounded parallel provider I/O."""

from asyncio import Semaphore, TaskGroup
from logging import getLogger

from papilio.errors.base import APPException

from ...domain.dtos.recheck import PaymentRecheck
from ...domain.results.check import RecheckStats
from ..interfaces.check import IPaymentCheckExecution
from .check import PaymentCheckPipeline

log = getLogger(__name__)


class PaymentRecheckPipeline:
    def __init__(
        self, execution: IPaymentCheckExecution, check: PaymentCheckPipeline
    ) -> None:
        """Bind the batch selector and the existing one-payment check."""
        self.execution = execution
        self.check = check

    async def run(self, query: PaymentRecheck) -> RecheckStats:
        """Claim one batch and check payments independently.

        Args:
            query: Validated batch size, retry spacing and concurrency.

        Returns:
            Counts of selected, confirmed and failed payment checks.
        """
        ids = await self.execution.claim(limit=query.limit, delay=query.delay)
        slots = Semaphore(query.concurrency)
        async with TaskGroup() as group:
            checks = [group.create_task(self._check(id, slots)) for id in ids]
        results = [task.result() for task in checks]
        return RecheckStats(
            selected=len(ids),
            confirmed=sum(result is True for result in results),
            failed=sum(result is None for result in results),
        )

    async def _check(self, id: int, slots: Semaphore) -> bool | None:
        result = None
        async with slots:
            try:
                payment = await self.check.check(id)
                result = payment.confirmed_at is not None
            except APPException as error:
                log.warning(
                    "Crypto payment %s check failed: %s",
                    id,
                    error.message_code,
                )
        return result
