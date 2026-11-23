"""Coordinate card prefix writes with authoritative bank references."""

from papilio.infra.db.tools.decorators import transactional
from pydantic_core import MISSING

from src.apps.shop.banking.banks.app.interfaces.queries import IBankQuery

from ...domain.dtos.records import CardPrefixCreate, CardPrefixUpdate
from ...domain.models.records import CardPrefixModel
from ..interfaces.records import ICardPrefixCRUD


class CardPrefixCommand:
    def __init__(self, prefixes: ICardPrefixCRUD, banks: IBankQuery) -> None:
        """Bind prefix writes and bank reads in the current request.

        Args:
            prefixes: Owning prefix record service.
            banks: Authoritative bank reference service.

        Returns:
            None.
        """
        self.prefixes = prefixes
        self.banks = banks

    @transactional
    async def create(self, data: CardPrefixCreate) -> CardPrefixModel:
        """Create a prefix under an existing bank.

        Args:
            data: Validated prefix fields and bank identity.

        Returns:
            The stored prefix; inactive banks remain valid references.

        Raises:
            NotFoundException: The bank is absent.
            ConflictException: The prefix already exists.
        """
        await self.banks.get_by_id(data.bank_id)
        record = await self.prefixes.create(data)
        return record

    @transactional
    async def update(self, id: int, data: CardPrefixUpdate) -> CardPrefixModel:
        """Update a prefix, checking a bank only when supplied.

        Args:
            id: Stored prefix identity.
            data: Validated patch preserving omitted fields.

        Returns:
            The updated prefix record.

        Raises:
            NotFoundException: The prefix or supplied bank is absent.
            ValidationException: No recognized patch fields were supplied.
            ConflictException: The requested prefix already exists.
        """
        if data.bank_id is not MISSING:
            await self.banks.get_by_id(data.bank_id)
        record = await self.prefixes.update(id, data)
        return record
