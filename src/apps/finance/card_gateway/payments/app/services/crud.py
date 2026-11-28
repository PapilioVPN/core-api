"""Read hosted payment status and store matching confirmation evidence."""

from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.dtos.paid import PaidTransfer
from ...domain.enums.records import PaymentStatus
from ...domain.models.records import PaymentModel
from ...domain.results.records import PaymentDetails
from ...infra.pg.repositories.crud import PaymentRepository


class PaymentService(IDChecks[PaymentModel]):
    entity = "CardGatewayPayment"

    def __init__(self, repo: PaymentRepository) -> None:
        self.repo = repo

    async def get_by_id(self, id: int) -> PaymentDetails:
        """Read current status from the committed local record.

        Args:
            id: Stored payment identity.

        Returns:
            Payment status and known amounts in whole rials.

        Raises:
            NotFoundException: The payment does not exist.
        """
        stored = await self.repo.get_by_id(id)
        payment = self._check_for_id_existence(id, stored)
        status = PaymentStatus.PENDING
        if payment.confirmed_at is not None:
            status = PaymentStatus.CONFIRMED
        elif (
            payment.expires_at is not None and payment.expires_at <= utc_now()
        ):
            status = PaymentStatus.EXPIRED
        return PaymentDetails(
            id=payment.id,
            gateway_id=payment.gateway_id,
            status=status,
            amount=payment.amount,
            paid_amount=payment.paid_amount,
            attempt_code=payment.attempt_code,
            pay_url=payment.pay_url,
            expires_at=payment.expires_at,
            confirmed_at=payment.confirmed_at,
        )

    async def confirm(
        self, gateway_id: int, transfer: PaidTransfer
    ) -> PaymentModel | None:
        """Apply matching paid evidence inside the invoking command's UoW.

        Args:
            gateway_id: Authenticated gateway account.
            transfer: Verified provider notification in whole rials.

        Returns:
            The newly confirmed payment, or None when it cannot be confirmed.
        """
        payment = await self.repo.confirm(
            gateway_id, transfer, confirmed_at=utc_now()
        )
        return payment
