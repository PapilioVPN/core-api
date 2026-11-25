"""Persist cryptocurrency payment records."""

from datetime import datetime

from papilio.tools.checks import IDChecks

from ...domain.models.quote import Quote
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.invoice import Invoice
from ...infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentService(IDChecks[CryptoPaymentModel]):
    entity = "CryptoPayment"

    def __init__(self, repo: CryptoPaymentRepository) -> None:
        """Bind the request's payment repository."""
        self.repo = repo

    async def create(self, data: CryptoPaymentModel) -> CryptoPaymentModel:
        """Persist a prepared payment in the caller's transaction.

        Args:
            data: Prepared payment record.

        Returns:
            The saved record with its generated identity.
        """
        payment = await self.repo.create(data)
        return payment

    async def get_by_id(self, id: int) -> CryptoPaymentModel:
        """Return the stored payment or report that it does not exist."""
        payment = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, payment)

    async def claim(
        self, *, now: datetime, before: datetime, limit: int
    ) -> tuple[int, ...]:
        """Mark and return at most one batch of due records."""
        ids = await self.repo.claim(now=now, before=before, limit=limit)
        return ids

    async def set_quote(
        self, id: int, data: Quote
    ) -> CryptoPaymentModel | None:
        """Save an unset quote in the caller's transaction."""
        payment = await self.repo.set_quote(id, data)
        return payment

    async def set_invoice(
        self, id: int, data: Invoice
    ) -> CryptoPaymentModel | None:
        """Attach a provider invoice in the caller's transaction.

        Args:
            id: Payment identity.
            data: Provider invoice identity and hosted URL.

        Returns:
            The updated payment, or None if an invoice is already stored.
        """
        payment = await self.repo.set_invoice(id, data)
        return payment

    async def confirm(
        self,
        id: int,
        invoice_id: str,
        settlement_id: str,
        confirmed_at: datetime,
    ) -> CryptoPaymentModel | None:
        """Confirm a payment against its unchanged original invoice.

        Args:
            id: Local payment identity.
            invoice_id: Original provider invoice identity.
            settlement_id: Provider operation that received the payment.
            confirmed_at: UTC confirmation time.

        Returns:
            The confirmed record, or None when the write no longer applies.
        """
        payment = await self.repo.confirm(
            id, invoice_id, settlement_id, confirmed_at
        )
        return payment
