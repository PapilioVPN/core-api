"""Claim due IPG payments and persist their bank reference once."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import select, update
from sqlmodel import col

from .....gateways.domain.enums.records import GatewayKind
from .....gateways.infra.pg.tables import IPGGatewayTable
from ....domain.enums.records import LinkStatus
from ....domain.models.records import PaymentModel
from ....domain.results.verify import CheckTarget
from ..tables import IPGPaymentTable


class VerifyRepository(PGPersistenceRepository[PaymentModel]):
    table = IPGPaymentTable

    async def claim(
        self, *, now: datetime, since: datetime, retry_at: datetime, limit: int
    ) -> tuple[CheckTarget, ...]:
        """Reserve a bounded batch and return the provider inputs.

        Args:
            now: Due cutoff in UTC.
            since: Earliest creation time eligible for automatic verification.
            retry_at: Earliest time any claimed payment can be checked again.
            limit: Maximum number of rows to claim.

        Returns:
            Claimed IDs, gateway kinds, rial terms and encrypted credentials.
        """
        table = self.table
        ready = (
            col(table.status) == LinkStatus.READY,
            col(table.next_check_at) <= now,
        )
        due = (
            select(col(table.id))
            .where(
                *ready,
                col(table.created_at) >= since,
                col(table.reference).is_not(None),
                col(table.credential).is_not(None),
            )
            .order_by(col(table.next_check_at), col(table.id))
            .limit(limit)
        )
        claims = (
            update(table)
            .where(col(table.id).in_(due), *ready)
            .values(next_check_at=retry_at)
            .returning(
                col(table.id),
                col(table.gateway_id),
                col(table.amount),
                col(table.reference),
                col(table.credential),
            )
            .cte("claimed")
        )
        gateway = IPGGatewayTable
        stmt = (
            select(
                claims.c.id,
                col(gateway.kind),
                claims.c.amount,
                claims.c.reference,
                claims.c.credential,
            )
            .join(gateway, col(gateway.id) == claims.c.gateway_id)
            .order_by(claims.c.id)
        )
        rows = await self.uow.execute(stmt)
        targets = tuple(CheckTarget(*row) for row in rows.tuples())
        return targets

    async def find(
        self, kind: GatewayKind, reference: str
    ) -> CheckTarget | None:
        """Resolve a callback token to a pending payment on that provider."""
        table = self.table
        gateway = IPGGatewayTable
        stmt = (
            select(
                col(table.id),
                col(gateway.kind),
                col(table.amount),
                col(table.reference),
                col(table.credential),
            )
            .join(gateway, col(gateway.id) == col(table.gateway_id))
            .where(
                col(gateway.kind) == kind,
                col(table.reference) == reference,
                col(table.status) == LinkStatus.READY,
            )
        )
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        target = None
        if row is not None:
            id, provider, amount, token, credential = row
            if token is not None and credential is not None:
                target = CheckTarget(id, provider, amount, token, credential)
        return target

    async def confirm(
        self, id: int, *, code: str, now: datetime
    ) -> PaymentModel | None:
        """Record verified evidence only for a payment still awaiting it.

        Args:
            id: Saved payment identity.
            code: Bank reference reported by the provider.
            now: UTC time the Core observed settlement.

        Returns:
            The newly confirmed record, or None on an already resolved attempt.
        """
        table = self.table
        stmt = (
            update(table)
            .where(col(table.id) == id, col(table.status) == LinkStatus.READY)
            .values(
                status=LinkStatus.CONFIRMED,
                tracking_code=code,
                confirmed_at=now,
                next_check_at=None,
            )
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment
