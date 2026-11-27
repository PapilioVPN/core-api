"""Check reserved payments in bounded batches."""

from asyncio import TaskGroup
from itertools import batched

from ...domain.dtos.recheck import PaymentRecheck
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.check import RecheckStats
from ..interfaces.check import IPaymentCheckExecution
from .check import PaymentCheckPipeline


class PaymentRecheckPipeline:
    def __init__(
        self, execution: IPaymentCheckExecution, check: PaymentCheckPipeline
    ) -> None:
        """Bind the batch selector and the one-payment check."""
        self.execution = execution
        self.check = check

    async def run(self, query: PaymentRecheck) -> RecheckStats:
        """Claim due payments and check each group independently.

        Args:
            query: Validated batch size, retry spacing and concurrency.

        Returns:
            Counts of selected, confirmed and unsuccessful checks.
        """
        ids = await self.execution.claim(limit=query.limit, delay=query.delay)
        confirmed = failed = 0
        for batch in batched(ids, query.concurrency):
            async with TaskGroup() as group:
                checks = [
                    group.create_task(self.check.check(id)) for id in batch
                ]
            for check in checks:
                result = check.result()
                if not isinstance(result, CryptoPaymentModel):
                    failed += 1
                elif result.confirmed_at is not None:
                    confirmed += 1
        return RecheckStats(
            selected=len(ids), confirmed=confirmed, failed=failed
        )
