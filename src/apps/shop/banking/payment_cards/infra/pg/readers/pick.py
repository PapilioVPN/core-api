"""Select an eligible receiving card against current banking references."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import func, select
from sqlmodel import col

from src.apps.shop.banking.banks.infra.pg.tables import BankTable
from src.apps.shop.banking.card_prefixes.infra.pg.sql.match import match_prefix

from ....domain.enums.records import PaymentMode
from ....domain.models.records import PaymentCardModel
from ..tables import PaymentCardTable


class CardPickReader(PGReader):
    async def pick(self, mode: PaymentMode) -> PaymentCardModel | None:
        """Pick one random active card for the requested mode.

        Args:
            mode: Manual or automatic payment.

        Returns:
            A card whose current active issuer matches its saved issuer.
            None when no card meets the requested mode and issuer conditions.
        """
        table = PaymentCardTable
        number = col(table.card_number)
        allowed = (
            col(table.allow_manual)
            if mode is PaymentMode.MANUAL
            else col(table.allow_auto)
        )
        match = (
            match_prefix(func.left(number, 6), func.left(number, 8))
            .correlate(table)
            .lateral()
        )
        stmt = (
            select(table)
            .join(match, match.c.bank_id == col(table.bank_id))
            .join(BankTable, col(BankTable.id) == col(table.bank_id))
            .where(
                col(table.is_active).is_(True),
                allowed.is_(True),
                match.c.is_active.is_(True),
                col(BankTable.is_active).is_(True),
            )
            .order_by(func.random())
            .limit(1)
        )
        result = await self.uow.execute(stmt)
        card = result.scalar_one_or_none()
        return card
