"""Persist crypto payments and resolve gateway invoice identities."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import and_
from sqlmodel import col

from ....domain.enums.records import CryptoPaymentStatus
from ....domain.models.records import CryptoPaymentModel
from ..tables import CryptoPaymentTable


class CryptoPaymentRepository(PGPersistenceRepository[CryptoPaymentModel]):
    table = CryptoPaymentTable

    async def set_invoice(
        self, id: int, *, invoice_id: str, invoice_url: str
    ) -> CryptoPaymentModel | None:
        """Attach the issued invoice to a pending payment once.

        Args:
            id: Stored crypto payment identity.
            invoice_id: Opaque invoice identity from the configured gateway.
            invoice_url: Hosted payment link returned by that gateway.

        Returns:
            The updated payment, or None if no pending unlinked row matched.
        """
        table = self.table
        rows = await self.update(
            and_(
                col(table.id) == id,
                col(table.status) == CryptoPaymentStatus.PENDING,
                col(table.invoice_id).is_(None),
            ),
            {"invoice_id": invoice_id, "invoice_url": invoice_url},
        )
        return rows[0] if rows else None

    async def find_by_invoice(
        self, gateway_id: int, invoice_id: str
    ) -> CryptoPaymentModel | None:
        """Resolve an invoice within its configured gateway account.

        Args:
            gateway_id: Stored identity of the issuing account.
            invoice_id: Opaque invoice identity from that account.

        Returns:
            The matched payment, or None when the invoice is unknown.
        """
        table = self.table
        payment = await self.get_one(
            col(table.gateway_id) == gateway_id,
            col(table.invoice_id) == invoice_id,
        )
        return payment

    async def record_status(
        self,
        id: int,
        *,
        states: tuple[CryptoPaymentStatus, ...],
        status: CryptoPaymentStatus,
        provider_payment_id: str | None,
        confirmed_at: datetime | None,
    ) -> CryptoPaymentModel | None:
        """Update one payment only while it is in an expected state.

        Args:
            id: Stored attempt identity.
            states: Previous states allowed by the payment operation.
            status: New payment state.
            provider_payment_id: Verified settling payment, if confirmed.
            confirmed_at: UTC confirmation time, if confirmed.

        Returns:
            The updated record, or None when the state no longer matches.
        """
        table = self.table
        rows = await self.update(
            and_(col(table.id) == id, col(table.status).in_(states)),
            {
                "status": status,
                "provider_payment_id": provider_payment_id,
                "confirmed_at": confirmed_at,
            },
        )
        return rows[0] if rows else None
