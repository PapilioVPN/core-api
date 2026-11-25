"""Write payment records and their decisions."""

from datetime import datetime

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

    async def get_by_id(self, id: int) -> PaymentModel:
        """Read a payment by its stored identity, or report absence."""
        payment = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, payment)

    async def create_auto(
        self, data: PaymentModel, digits: int
    ) -> PaymentModel | None:
        """Attempt one reservation for a prepared automatic payment."""
        payment = await self.repo.create_auto(data, digits)
        return payment

    async def confirm_auto(
        self, amount: int, *, since: datetime, until: datetime
    ) -> PaymentModel | None:
        """Apply one matched deposit inside the caller's transaction."""
        payment = await self.repo.confirm_auto(
            amount, since=since, until=until, confirmed_at=utc_now()
        )
        return payment

    async def review(
        self,
        id: int,
        status: PaymentStatus,
        *,
        confirmed_at: datetime | None,
        reason: str | None = None,
    ) -> PaymentModel | None:
        """Apply a prepared decision to a pending payment.

        Args:
            id: Stored payment identity.
            status: Confirmed or rejected state.
            confirmed_at: Prepared UTC timestamp for confirmation, if any.
            reason: Optional explanation for a rejection.

        Returns:
            The updated payment, or None when no pending record matches.
        """
        payment = await self.repo.review(
            id,
            status,
            confirmed_at=confirmed_at,
            reason=reason,
        )
        return payment
