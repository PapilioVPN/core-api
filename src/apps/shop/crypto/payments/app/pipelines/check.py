"""Confirm a Plisio payment only from matching provider evidence."""

from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure

from ...domain.models.records import CryptoPaymentModel
from ...domain.results.check import Operation, OperationStatus, PlisioCheck
from ...domain.results.records import PaymentFailure
from ..interfaces.check import IPaymentCheckExecution
from ..interfaces.gateways import IPlisioGateway


def _matches(
    operation: Operation, payment: CryptoPaymentModel, parent: str | None
) -> bool:
    return (
        operation.status is OperationStatus.COMPLETED
        and operation.parent_id == parent
        and operation.order_id == str(payment.id)
        and operation.quote_amount == payment.quote_amount
        and operation.quote_currency == payment.quote_currency
        and operation.expected is not None
        and operation.expected > 0
        and operation.received is not None
        and operation.received >= operation.expected
    )


class PaymentCheckPipeline:
    def __init__(
        self, execution: IPaymentCheckExecution, plisio: IPlisioGateway
    ) -> None:
        """Bind the payment phases and authenticated provider reads."""
        self.execution = execution
        self.plisio = plisio

    async def check(
        self, id: int
    ) -> CryptoPaymentModel | ConfigFailure | PaymentFailure:
        """Check an issued payment, leaving unverified payments unchanged.

        Args:
            id: Local payment identity.

        Returns:
            The stored payment or an expected check failure.
        """
        prepared = await self.execution.prepare(id)
        if isinstance(prepared, PlisioCheck):
            payment: CryptoPaymentModel | ConfigFailure | PaymentFailure = (
                prepared.payment
            )
            settlement = await self._settlement(prepared)
            if isinstance(settlement, PaymentFailure):
                payment = settlement
            elif settlement is not None:
                payment = await self.execution.complete(
                    id, prepared.invoice_id, settlement
                )
        else:
            payment = prepared
        return payment

    async def _settlement(
        self, data: PlisioCheck
    ) -> str | PaymentFailure | None:
        original = await self.plisio.read(data.config, data.invoice_id)
        settlement: str | PaymentFailure | None = None
        if isinstance(original, PaymentFailure):
            settlement = original
        elif _matches(original, data.payment, None):
            settlement = original.id
        elif (
            original.parent_id is None
            and original.status is OperationStatus.REPLACED
        ):
            for id in dict.fromkeys(original.child_ids):
                child = await self.plisio.read(data.config, id)
                if isinstance(child, PaymentFailure):
                    settlement = child
                    break
                if _matches(child, data.payment, original.id):
                    settlement = child.id
                    break
        return settlement
