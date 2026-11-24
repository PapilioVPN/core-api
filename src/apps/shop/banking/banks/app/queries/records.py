"""Read bank references for the panel and resolve known issuers."""

from collections.abc import Sequence

from papilio.core import resources
from papilio.errors.exceptions import NotFoundException
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import BankList
from ...domain.models.records import BankModel
from ...domain.results.prefix import BankMatch
from ...infra.pg.readers.records import BankPrefixReader
from ...infra.pg.repositories.records import BankRepository


class BankQuery(IDChecks[BankModel]):
    entity = "Bank"

    def __init__(
        self, repo: BankRepository, prefixes: BankPrefixReader
    ) -> None:
        """Bind bank reads to the request.

        Args:
            repo: PostgreSQL bank record operations.
            prefixes: Issuer lookup using stored card prefixes.

        Returns:
            None.
        """
        self.repo = repo
        self.prefixes = prefixes

    async def get_by_id(self, id: int) -> BankModel:
        """Read a bank by identity.

        Args:
            id: Stored bank identity.

        Returns:
            The matching reference.

        Raises:
            NotFoundException: The bank does not exist.
        """
        bank = await self.repo.get_by_id(id)
        bank = self._check_for_id_existence(id, bank)
        return bank

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[BankModel]:
        """Read several bank references.

        Args:
            ids: Bounded sequence of stored identities.

        Returns:
            Unique matches, omitting missing identities.
        """
        banks = await self.repo.get_by_ids(ids) if ids else []
        return banks

    async def find_by_prefix(self, prefix: str) -> BankMatch | None:
        """Resolve the offline issuer for a prefix.

        Args:
            prefix: Six or eight ASCII digits.

        Returns:
            The issuer and prefix activity, or None if unknown.
        """
        match = await self.prefixes.find_by_prefix(prefix)
        return match

    async def get_by_prefix(self, prefix: str) -> BankMatch:
        """Resolve a required issuer by prefix.

        Args:
            prefix: Six or eight ASCII digits.

        Returns:
            The issuer and prefix activity.

        Raises:
            NotFoundException: The prefix is unknown.
        """
        match = await self.find_by_prefix(prefix)
        if match is None:
            raise NotFoundException(
                message="No bank matches this card prefix.",
                message_code=resources.NOT_FOUND_ERROR,
                entity=self.entity,
                identifier="prefix",
                identifier_value=prefix,
            )
        return match

    async def list(self, query: BankList) -> PagedType[BankModel]:
        """Read one panel page with reference search and activity filters.

        Args:
            query: Validated search, activity and pagination inputs.

        Returns:
            The ordered bank page and its total count.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            is_active=query.is_active,
        )
        return page
