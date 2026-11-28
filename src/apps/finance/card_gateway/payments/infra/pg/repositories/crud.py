"""Persist hosted card payments and their provider link."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import or_, update
from sqlmodel import col

from ....domain.dtos.paid import PaidTransfer
from ....domain.models.records import PaymentModel
from ..tables import CardGatewayPaymentTable


class PaymentRepository(PGPersistenceRepository[PaymentModel]):
    table = CardGatewayPaymentTable

    async def find_by_slug(
        self, gateway_id: int, slug: str
    ) -> PaymentModel | None:
        """Read a payment by the scoped provider link identifier.

        Args:
            gateway_id: Identity of the gateway account that issued the link.
            slug: Exact identifier returned by the provider.

        Returns:
            The matching payment, or None when there is no matching link.
        """
        table = self.table
        payment = await self.get_one(
            col(table.gateway_id) == gateway_id, col(table.slug) == slug
        )
        return payment

    async def claim_link(self, id: int, *, requested_at: datetime) -> bool:
        """Record the first outbound attempt before contacting the provider.

        Args:
            id: Stored payment identity.
            requested_at: Time of the dispatch claim in UTC.

        Returns:
            Whether this operation acquired the link creation claim.
        """
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.slug).is_(None),
                col(table.link_requested_at).is_(None),
            )
            .values(link_requested_at=requested_at)
            .returning(col(table.id))
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        claimed = result.scalar_one_or_none() is not None
        return claimed

    async def release_link(self, id: int) -> bool:
        """Clear a claim after an outcome that proves no link was issued.

        Args:
            id: Identity of the payment whose creation was rejected.

        Returns:
            Whether the unlinked payment's claim was released.
        """
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.slug).is_(None),
                col(table.link_requested_at).is_not(None),
            )
            .values(link_requested_at=None)
            .returning(col(table.id))
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        released = result.scalar_one_or_none() is not None
        return released

    async def save_link(
        self,
        id: int,
        *,
        slug: str,
        pay_url: str,
        expires_at: datetime | None,
    ) -> PaymentModel | None:
        """Record the first issued link on a payment.

        Args:
            id: Stored payment identity.
            slug: Exact identifier returned by the provider.
            pay_url: Validated hosted payment URL.
            expires_at: Provider expiration in UTC, or None for no expiry.

        Returns:
            The updated payment, or None for an absent or linked payment.

        Raises:
            IntegrityError: This gateway already uses the slug on a payment.
        """
        table = self.table
        stmt = (
            update(table)
            .where(col(table.id) == id, col(table.slug).is_(None))
            .values(slug=slug, pay_url=pay_url, expires_at=expires_at)
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
        gateway_id: int,
        transfer: PaidTransfer,
        *,
        confirmed_at: datetime,
    ) -> PaymentModel | None:
        """Apply matching paid evidence to an unconfirmed issued link.

        Args:
            gateway_id: Authenticated account that issued the payment link.
            transfer: Verified provider amounts in rials and notification time.
            confirmed_at: Local decision timestamp in UTC.

        Returns:
            The updated payment, or None when the guarded update has no match.
        """
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.gateway_id) == gateway_id,
                col(table.slug) == transfer.slug,
                col(table.pay_url).is_not(None),
                col(table.amount) == transfer.base_amount,
                col(table.confirmed_at).is_(None),
                or_(
                    col(table.expires_at).is_(None),
                    col(table.expires_at) > transfer.sent_at,
                ),
            )
            .values(
                paid_amount=transfer.paid_amount,
                attempt_code=transfer.attempt_code,
                confirmed_at=confirmed_at,
            )
            .returning(table)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment
