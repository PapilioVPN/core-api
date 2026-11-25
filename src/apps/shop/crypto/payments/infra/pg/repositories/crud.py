"""Persist cryptocurrency payment records."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from sqlalchemy import update
from sqlmodel import col

from ....domain.models.quote import Quote
from ....domain.models.records import CryptoPaymentModel
from ....domain.results.invoice import Invoice
from ..tables import CryptoPaymentTable


class CryptoPaymentRepository(PGIdentifiedRepository[CryptoPaymentModel]):
    table = CryptoPaymentTable

    async def set_quote(
        self, id: int, data: Quote
    ) -> CryptoPaymentModel | None:
        """Store a quote only while the original payment has no quote."""
        table = self.table
        stmt = (
            update(table)
            .where(col(table.id) == id, col(table.quote_amount).is_(None))
            .values(
                quote_amount=data.amount,
                quote_currency=data.currency,
                quote_rate=data.rate,
            )
            .returning(table)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment

    async def set_invoice(
        self, id: int, data: Invoice
    ) -> CryptoPaymentModel | None:
        """Attach the first invoice for an existing quoted payment.

        Args:
            id: Payment identity.
            data: Provider invoice identity and hosted URL.

        Returns:
            The updated payment or None if no row matched.
        """
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.quote_amount).is_not(None),
                col(table.invoice_id).is_(None),
            )
            .values(invoice_id=data.id, invoice_url=data.url)
            .returning(table)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment
