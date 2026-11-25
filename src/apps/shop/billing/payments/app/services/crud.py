"""Write payment records and their decisions."""

from datetime import datetime

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.enums.records import PaymentStatus
from ...domain.models.records import PaymentModel
from ...infra.pg.repositories.crud import PaymentRepository


class PaymentService(IDChecks[PaymentModel]):
    entity = "Payment"

    def __init__(self, repo: PaymentRepository) -> None:
        """Bind the request's payment repository."""
        self.repo = repo

    @transactional
    async def create(self, data: PaymentModel) -> PaymentModel:
        """Register one payment against its receipt.

        Args:
            data: Prepared payment with its receipt ID and amount in rials.

        Returns:
            Stored payment with its identity and timestamps.
        """
        payment = await self.repo.create(data)
        return payment

    @transactional
    async def create_auto(
        self, data: PaymentModel, digits: int
    ) -> PaymentModel:
        """Reserve one previously unused transfer amount near the price."""
        payment = None
        for _ in range(3):
            payment = await self.repo.create_auto(data, digits)
            if payment is not None:
                break
        if payment is None:
            raise ConflictException(
                message="No transfer amount is available for this payment",
                message_code="transfer_amount_unavailable",
                unique_dict={"amount": data.amount},
            )
        return payment

    async def confirm_auto(
        self, amount: int, *, since: datetime, until: datetime
    ) -> PaymentModel | None:
        """Apply one matched deposit inside the caller's transaction."""
        payment = await self.repo.confirm_auto(
            amount, since=since, until=until, confirmed_at=utc_now()
        )
        return payment

    @transactional
    async def review(
        self, id: int, status: PaymentStatus, *, reason: str | None = None
    ) -> PaymentModel:
        """Apply the decision to a pending payment.

        Args:
            id: Stored payment identity.
            status: Confirmed or rejected state.
            reason: Optional explanation for a rejection.

        Returns:
            The updated payment, with a timestamp on confirmation.

        Raises:
            NotFoundException: The payment does not exist.
            ConflictException: The payment is no longer pending.
        """
        payment = await self.repo.review(
            id,
            status,
            confirmed_at=utc_now()
            if status == PaymentStatus.CONFIRMED
            else None,
            reason=reason,
        )
        if payment is None:
            existing = await self.repo.get_by_id(id)
            self._check_for_id_existence(id, existing)
            raise ConflictException(
                message="The payment has already been reviewed",
                message_code="payment_already_reviewed",
                unique_dict={"id": id},
            )
        return payment
