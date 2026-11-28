"""Check due IPG payments in bounded concurrent batches."""

from asyncio import TaskGroup
from itertools import batched

from ....gateways.app.interfaces.configs import IGatewayConfigCodec
from ....gateways.domain.enums.records import GatewayKind
from ...domain.dtos.verify import VerifyPolicy
from ...domain.models.records import PaymentModel
from ...domain.results.verify import CheckTarget, Verification, VerifyBatch
from ..executions.verify import VerifyExecution
from ..interfaces.create import IZarinPalClient, IZibalClient


class VerifyPipeline:
    def __init__(
        self,
        execution: VerifyExecution,
        zarinpal: IZarinPalClient,
        zibal: IZibalClient,
        codec: IGatewayConfigCodec,
    ) -> None:
        self.execution = execution
        self.clients = {
            GatewayKind.ZARINPAL: zarinpal,
            GatewayKind.ZIBAL: zibal,
        }
        self.codec = codec

    async def run(self, policy: VerifyPolicy) -> VerifyBatch:
        """Check a bounded set and count committed confirmations."""
        targets = await self.execution.claim(policy)
        confirmed = 0
        for batch in batched(targets, policy.parallel):
            async with TaskGroup() as group:
                checks = [
                    group.create_task(self.check(target)) for target in batch
                ]
            confirmed += sum(task.result() is not None for task in checks)
        return VerifyBatch(selected=len(targets), confirmed=confirmed)

    async def check(self, target: CheckTarget) -> PaymentModel | None:
        """Verify outside SQL, then commit the bank reference if present."""
        merchant = self.codec.open({"merchant_id": target.credential})
        payment = None
        if merchant is not None:
            code = await self.clients[target.kind].verify(
                Verification(
                    target.id, target.amount, target.reference, merchant
                ),
            )
            if code and len(code) <= 128:
                payment = await self.execution.confirm(target.id, code)
        return payment
