"""Store and read card payments through native PostgreSQL persistence."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import and_, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from ....domain.dtos.records import CardPaymentList
from ....domain.enums.records import PaymentMode, PaymentStatus
from ....domain.models.records import CardPaymentModel
from ..tables import AMOUNT_CONSTRAINT, CardPaymentTable


class CardPaymentRepository(PGPersistenceRepository[CardPaymentModel]):
    table = CardPaymentTable

    async def reserve(self, data: CardPaymentModel) -> CardPaymentModel | None:
        """Insert an automatic payment unless its amount already overlaps.

        Args:
            data: Prepared payment with an exact amount and expiry.

        Returns:
            The new row, or None when its amount is already reserved.
        """
        stmt = (
            insert(self.table)
            .values(data.to_row())
            .on_conflict_do_nothing(constraint=AMOUNT_CONSTRAINT)
            .returning(self.table)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def reserved_amounts(
        self, *, first: int, last: int, expires_at: datetime
    ) -> set[int]:
        """Project occupied amounts using the transaction's start time.

        Args:
            first: Inclusive lower amount in rials.
            last: Inclusive upper amount in rials.
            expires_at: Exclusive upper time bound of the proposed payment.

        Returns:
            A set of occupied amounts from overlapping automatic payments.
        """
        table = self.table
        amount = col(table.payable_amount)
        stmt = select(amount).where(
            col(table.mode) == PaymentMode.AUTO,
            amount.between(first, last),
            col(table.created_at) < expires_at,
            col(table.expires_at) > func.current_timestamp(),
        )
        result = await self.uow.execute(stmt)
        return {value for value in result.scalars() if value is not None}

    async def list(
        self,
        data: CardPaymentList,
        *,
        as_of: datetime,
        limit: int,
        offset: int,
    ) -> PagedType[CardPaymentModel]:
        """Read a page of payments in descending identity order.

        Args:
            data: Exact payment filters and optional creation time bounds.
            as_of: Instant used to evaluate automatic payment expiry.
            limit: Maximum matching rows to return.
            offset: Matching rows to skip.

        Returns:
            The filtered page and its unpaged count.
        """
        table = self.table
        exact = (
            (col(table.card_id), data.card_id),
            (col(table.status), data.status),
            (col(table.mode), data.mode),
            (col(table.code), data.code),
            (col(table.amount), data.amount),
            (col(table.payable_amount), data.payable_amount),
            (col(table.transfer_id), data.transfer_id),
        )
        where: list[ColumnElement[bool]] = [
            column == value for column, value in exact if value is not None
        ]
        if data.since is not None:
            where.append(col(table.created_at) >= data.since)
        if data.until is not None:
            where.append(col(table.created_at) < data.until)
        if data.expired is not None:
            expires_at = col(table.expires_at)
            where.append(col(table.mode) == PaymentMode.AUTO)
            where.append(
                expires_at <= as_of if data.expired else expires_at > as_of
            )
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

    async def review(
        self,
        id: int,
        status: PaymentStatus,
        *,
        decided_at: datetime,
        reason: str | None,
    ) -> CardPaymentModel | None:
        """Store a decision with one conditional update.

        Args:
            id: Stored payment identity.
            status: Prepared terminal state.
            decided_at: UTC instant of the decision.
            reason: Optional rejection reason.

        Returns:
            The updated payment, or None if it is missing or no longer pending.
        """
        table = self.table
        rows = await self.update(
            and_(
                col(table.id) == id, col(table.status) == PaymentStatus.PENDING
            ),
            {
                "status": status,
                "decided_at": decided_at,
                "rejection_reason": reason,
            },
        )
        return rows[0] if rows else None

    async def confirm_auto(
        self,
        *,
        transfer_id: int,
        card_id: int,
        amount: int,
        transferred_at: datetime,
        decided_at: datetime,
    ) -> CardPaymentModel | None:
        """Confirm exactly one eligible payment and link its evidence.

        Args:
            transfer_id: Stored incoming transfer identity.
            card_id: Destination card identity.
            amount: Received amount in whole rials.
            transferred_at: Bank timestamp used against the validity interval.
            decided_at: Current UTC confirmation timestamp.

        Returns:
            The changed payment, or None for an absent, ambiguous or decided
            match.
        """
        table = self.table
        pending_auto = (
            col(table.mode) == PaymentMode.AUTO,
            col(table.status) == PaymentStatus.PENDING,
            col(table.transfer_id).is_(None),
        )
        candidates = (
            select(col(table.id))
            .where(
                *pending_auto,
                col(table.card_id) == card_id,
                col(table.payable_amount) == amount,
                col(table.created_at) <= transferred_at,
                col(table.expires_at) > transferred_at,
            )
            .limit(2)
            .subquery()
        )
        matched = (
            select(func.min(candidates.c.id))
            .having(func.count() == 1)
            .scalar_subquery()
        )
        stmt = (
            update(table)
            .where(col(table.id) == matched, *pending_auto)
            .values(
                status=PaymentStatus.CONFIRMED,
                decided_at=decided_at,
                transfer_id=transfer_id,
            )
            .returning(table)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()
