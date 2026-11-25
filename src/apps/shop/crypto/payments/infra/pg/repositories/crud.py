"""Persist crypto payments and resolve gateway invoice identities."""

from collections.abc import Sequence
from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import and_, func, literal, select, update
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from src.apps.shop.crypto.gateways.infra.pg.tables import CryptoGatewayTable

from ....domain.enums.records import CryptoPaymentStatus
from ....domain.models.records import CryptoPaymentModel
from ..tables import CryptoPaymentTable


class CryptoPaymentRepository(PGPersistenceRepository[CryptoPaymentModel]):
    table = CryptoPaymentTable

    async def search(
        self,
        *,
        limit: int,
        offset: int,
        gateway_id: int | None,
        status: CryptoPaymentStatus | None,
        amount: int | None,
        invoice_id: str | None,
        provider_payment_id: str | None,
        has_invoice: bool | None,
        created_since: datetime | None,
        created_until: datetime | None,
    ) -> PagedType[CryptoPaymentModel]:
        """Page stored crypto payment attempts.

        Args:
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            gateway_id: Exact issuing account identity.
            status: Exact internal payment state.
            amount: Exact original amount in rials.
            invoice_id: Exact provider invoice reference.
            provider_payment_id: Exact confirmed provider payment reference.
            has_invoice: Whether an invoice is attached, if specified.
            created_since: Inclusive creation time bound.
            created_until: Exclusive creation time bound.

        Returns:
            Matching attempts in descending identity order and their total.
        """
        table = self.table
        where: list[ColumnElement[bool]] = []
        if gateway_id is not None:
            where.append(col(table.gateway_id) == gateway_id)
        if status is not None:
            where.append(col(table.status) == status)
        if amount is not None:
            where.append(col(table.amount) == amount)
        if invoice_id is not None:
            where.append(col(table.invoice_id) == invoice_id)
        if provider_payment_id is not None:
            where.append(col(table.provider_payment_id) == provider_payment_id)
        if has_invoice is not None:
            invoice = col(table.invoice_id)
            where.append(
                invoice.is_not(None) if has_invoice else invoice.is_(None)
            )
        if created_since is not None:
            where.append(col(table.created_at) >= created_since)
        if created_until is not None:
            where.append(col(table.created_at) < created_until)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

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

    async def take_due(
        self, *, kind: str, now: datetime, before: datetime, limit: int
    ) -> Sequence[CryptoPaymentModel]:
        """Move one batch to the back of the polling queue.

        Args:
            kind: Provider that can be queried by invoice identity.
            now: UTC timestamp to record before attempting the remote checks.
            before: Latest eligible creation or previous check timestamp.
            limit: Maximum rows to claim without loading the rest of the queue.

        Returns:
            The records reserved for this run, without a total count.
        """
        table = self.table
        gateway = CryptoGatewayTable
        due_at = func.coalesce(col(table.checked_at), col(table.created_at))
        due = (
            col(table.invoice_id).is_not(None),
            col(table.status).in_(
                (
                    literal(
                        CryptoPaymentStatus.PENDING.value, literal_execute=True
                    ),
                    literal(
                        CryptoPaymentStatus.PARTIAL.value, literal_execute=True
                    ),
                )
            ),
            due_at <= before,
        )
        ids = (
            select(col(table.id))
            .where(
                *due,
                col(table.gateway_id).in_(
                    select(col(gateway.id)).where(col(gateway.kind) == kind)
                ),
            )
            .order_by(due_at, col(table.id))
            .limit(limit)
        )
        stmt = (
            update(table)
            .where(col(table.id).in_(ids), *due)
            .values(checked_at=now)
            .returning(table)
            .execution_options(populate_existing=True)
        )
        result = await self.uow.execute(stmt)
        batch = result.scalars().all()
        return batch

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
