"""Native payment card persistence and conflict handling."""

from collections.abc import Mapping
from typing import Any

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy.exc import IntegrityError
from sqlmodel import col

from ....domain.models.records import PaymentCardModel
from ..tables import PaymentCardTable


def _duplicate() -> ConflictException:
    """Report a card uniqueness conflict without echoing its number."""
    return ConflictException(
        message="This payment card is already registered.",
        message_code="payment_card_exists",
        unique_dict={},
    )


class PaymentCardRepository(PGPersistenceRepository[PaymentCardModel]):
    table = PaymentCardTable

    async def create(self, data: PaymentCardModel) -> PaymentCardModel:
        """Insert a receiving card.

        Args:
            data: Prepared card record.

        Returns:
            The stored card.

        Raises:
            ConflictException: The number is already registered.
        """
        try:
            card = await super().create(data)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) != "23505":
                raise
            raise _duplicate() from None
        return card

    async def update_by_id(
        self, id: int, changes: Mapping[str, Any]
    ) -> PaymentCardModel | None:
        """Update one receiving card.

        Args:
            id: Stored card identity.
            changes: Supplied fields and their prepared column values.

        Returns:
            The updated card, or None if absent.

        Raises:
            ConflictException: Another card uses the number.
        """
        try:
            card = await super().update_by_id(id, changes)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) != "23505":
                raise
            raise _duplicate() from None
        return card

    async def find_by_number(self, number: str) -> PaymentCardModel | None:
        """Read the card matching the unique destination number.

        Args:
            number: Exact destination card number.

        Returns:
            The matching card, or None if the number is not registered.
        """
        card = await self.get_one(col(self.table.card_number) == number)
        return card

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        bank_id: int | None,
        is_active: bool | None,
        allow_manual: bool | None,
        allow_auto: bool | None,
    ) -> PagedType[PaymentCardModel]:
        """Read a filtered payment card page.

        Args:
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            q: Optional literal substring of the holder name.
            bank_id: Optional issuer identity.
            is_active: Optional card activity filter.
            allow_manual: Optional manual payment configuration filter.
            allow_auto: Optional automatic payment configuration filter.

        Returns:
            Matching cards in descending ID order and the unpaged count.
        """
        table = self.table
        where = []
        if q is not None:
            where.append(col(table.holder_name).icontains(q, autoescape=True))
        if bank_id is not None:
            where.append(col(table.bank_id) == bank_id)
        if is_active is not None:
            where.append(col(table.is_active).is_(is_active))
        if allow_manual is not None:
            where.append(col(table.allow_manual).is_(allow_manual))
        if allow_auto is not None:
            where.append(col(table.allow_auto).is_(allow_auto))
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page
