"""Read joined payment and receipt details from PostgreSQL."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import select
from sqlmodel import col

from src.apps.shop.billing.receipts.infra.pg.tables import ReceiptTable

from ....domain.results.details import PaymentDetail
from ..tables import PaymentTable


class PaymentReader(PGReader):
    async def get_by_id(self, id: int) -> PaymentDetail | None:
        """Read the payment and its receipt in one query.

        Args:
            id: Stored payment identity.

        Returns:
            Joined payment detail, or None if the payment is absent.
        """
        stmt = (
            select(PaymentTable, ReceiptTable)
            .outerjoin(
                ReceiptTable,
                col(ReceiptTable.id) == col(PaymentTable.receipt_id),
            )
            .where(col(PaymentTable.id) == id)
        )
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return PaymentDetail(*row) if row is not None else None
