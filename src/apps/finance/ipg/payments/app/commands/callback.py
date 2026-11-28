"""Verify a provider redirect using stored evidence."""

from ....gateways.domain.enums.records import GatewayKind
from ...domain.models.records import PaymentModel
from ..executions.verify import VerifyExecution
from ..pipelines.verify import VerifyPipeline


class VerifyCallbackCommand:
    def __init__(
        self, execution: VerifyExecution, pipeline: VerifyPipeline
    ) -> None:
        self.execution = execution
        self.pipeline = pipeline

    async def verify(
        self, kind: GatewayKind, reference: str
    ) -> PaymentModel | None:
        """Verify a callback against the stored provider reference.

        Args:
            kind: Provider identified by the callback route.
            reference: Provider token sent with the redirect.

        Returns:
            The confirmed payment if the provider attests settlement.
        """
        target = await self.execution.find(kind, reference)
        payment = None
        if target is not None:
            payment = await self.pipeline.check(target)
        return payment
