"""Native PostgreSQL payment persistence and filtered record reads."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import (
    BigInteger,
    String,
    and_,
    cast,
    exists,
    func,
    literal,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from src.apps.shop.billing.deposits.infra.pg.tables import DepositTable

from ....domain.enums.records import PaymentStatus
from ....domain.models.records import PaymentModel
from ..sql.auto import candidates
from ..tables import PaymentTable


class PaymentRepository(PGPersistenceRepository[PaymentModel]):
    table = PaymentTable

    async def attach_receipt(
        self, id: int, receipt_id: int
    ) -> PaymentModel | None:
        """Attach the first receipt only while the payment is pending."""
        table = self.table
        rows = await self.update(
            and_(
                col(table.id) == id,
                col(table.status) == PaymentStatus.PENDING,
                col(table.receipt_id).is_(None),
            ),
            {"receipt_id": receipt_id},
        )
        return rows[0] if rows else None

    async def create_auto(
        self, data: PaymentModel, digits: int
    ) -> PaymentModel | None:
        """Insert a transfer instruction or report a concurrent collision."""
        table = self.table
        candidate = candidates(data.amount, digits).subquery()
        value = candidate.c.value
        stmt = (
            insert(table)
            .from_select(
                [
                    "receipt_id",
                    "amount",
                    "status",
                    "transfer_amount",
                    "confirmation_code",
                ],
                select(
                    literal(data.receipt_id, type_=BigInteger),
                    literal(data.amount, type_=BigInteger),
                    literal(PaymentStatus.PENDING.value),
                    value,
                    func.lpad(cast(value % (10**digits), String), digits, "0"),
                ),
            )
            .on_conflict_do_nothing(
                index_elements=[col(table.transfer_amount)]
            )
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment

    async def confirm_auto(
        self,
        amount: int,
        *,
        since: datetime,
        until: datetime,
        confirmed_at: datetime,
    ) -> PaymentModel | None:
        """Confirm the pending payment bearing this exact transfer amount."""
        table = self.table
        earlier_report = exists(
            select(1)
            .where(
                col(DepositTable.amount) == amount,
                col(DepositTable.created_at) < col(table.created_at),
            )
            .correlate(table)
        )
        predicates = [
            col(table.transfer_amount) == amount,
            col(table.status) == PaymentStatus.PENDING,
            col(table.created_at) >= since,
            col(table.created_at) <= until,
            ~earlier_report,
        ]
        rows = await self.update(
            and_(*predicates),
            {"status": PaymentStatus.CONFIRMED, "confirmed_at": confirmed_at},
        )
        return rows[0] if rows else None

    async def review(
        self,
        id: int,
        status: PaymentStatus,
        *,
        confirmed_at: datetime | None,
        reason: str | None,
    ) -> PaymentModel | None:
        """Update one pending payment, returning None when no row changes."""
        table = self.table
        rows = await self.update(
            and_(
                col(table.id) == id, col(table.status) == PaymentStatus.PENDING
            ),
            {
                "status": status,
                "confirmed_at": confirmed_at,
                "rejection_reason": reason,
            },
        )
        return rows[0] if rows else None

    async def find_by_receipt_id(self, receipt_id: int) -> PaymentModel | None:
        """Read the payment that owns a receipt.

        Args:
            receipt_id: Stored receipt identity.

        Returns:
            The associated payment, or None when absent.
        """
        payment = await self.get_one(col(self.table.receipt_id) == receipt_id)
        return payment

    async def search(
        self,
        *,
        limit: int,
        offset: int = 0,
        status: PaymentStatus | None = None,
        amount: int | None = None,
        receipt_id: int | None = None,
        created_since: datetime | None = None,
        created_until: datetime | None = None,
    ) -> PagedType[PaymentModel]:
        """Read matching payments in descending identity order.

        Args:
            limit: Maximum number of payments to return.
            offset: Matching payments to skip.
            status: Exact payment state.
            amount: Exact expected amount in rials.
            receipt_id: Exact receipt identity.
            created_since: Inclusive payment creation time bound.
            created_until: Exclusive payment creation time bound.

        Returns:
            Matching payments and the count before pagination.
        """
        table = self.table
        where: list[ColumnElement[bool]] = []
        if status is not None:
            where.append(col(table.status) == status)
        if amount is not None:
            where.append(col(table.amount) == amount)
        if receipt_id is not None:
            where.append(col(table.receipt_id) == receipt_id)
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
