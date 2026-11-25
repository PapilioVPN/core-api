"""Persist cryptocurrency payment records."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from sqlalchemy import or_, update
from sqlmodel import col, select

from src.apps.shop.crypto.gateways.infra.pg.tables import CryptoGatewayTable

from ....domain.models.quote import Quote
from ....domain.models.records import CryptoPaymentModel
from ....domain.results.invoice import Invoice
from ..tables import CryptoPaymentTable


class CryptoPaymentRepository(PGIdentifiedRepository[CryptoPaymentModel]):
    table = CryptoPaymentTable

    async def claim(
        self, *, now: datetime, before: datetime, limit: int
    ) -> tuple[int, ...]:
        """Mark one due batch before releasing its transaction.

        Args:
            now: Current UTC check start time.
            before: Inclusive UTC cutoff for earlier attempts.
            limit: Maximum records selected for the batch.

        Returns:
            The IDs of outstanding Plisio payments reserved for this attempt.
        """
        table = self.table
        gateway = CryptoGatewayTable
        last = col(table.last_check_at)
        pending = (
            col(table.confirmed_at).is_(None),
            col(table.invoice_id).is_not(None),
            or_(last.is_(None), last <= before),
        )
        ids = (
            select(col(table.id))
            .join(gateway, col(gateway.id) == col(table.gateway_id))
            .where(*pending, col(gateway.kind) == "plisio")
            .order_by(last.nulls_first(), col(table.id))
            .limit(limit)
        )
        stmt = (
            update(table)
            .where(col(table.id).in_(ids), *pending)
            .values(last_check_at=now)
            .returning(col(table.id))
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        return tuple(result.scalars().all())

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

    async def confirm(
        self,
        id: int,
        invoice_id: str,
        settlement_id: str,
        confirmed_at: datetime,
    ) -> CryptoPaymentModel | None:
        """Attach the first verified settlement for the same invoice."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.invoice_id) == invoice_id,
                col(table.confirmed_at).is_(None),
            )
            .values(settlement_id=settlement_id, confirmed_at=confirmed_at)
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
