"""Card prefix records using native transactions, checks and conflicts."""

from collections.abc import Sequence

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import (
    CardPrefixCreate,
    CardPrefixList,
    CardPrefixUpdate,
)
from ...domain.models.records import CardPrefixModel
from ...infra.pg.repositories.crud import CardPrefixRepository


class CardPrefixCRUD(IDChecks[CardPrefixModel]):
    entity = "CardPrefix"

    def __init__(self, repo: CardPrefixRepository) -> None:
        """Bind the card prefix repository for the current unit of work.

        Args:
            repo: Native PostgreSQL card prefix repository.

        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts(entity="CardPrefix")
    @transactional
    async def create(self, data: CardPrefixCreate) -> CardPrefixModel:
        """Create a record with a unique numeric prefix.

        Args:
            data: Validated record fields and trusted existing bank identity.

        Returns:
            The stored prefix record with its database identity and timestamps.

        Raises:
            ConflictException: The prefix already exists.
        """
        record = await self.repo.create(
            CardPrefixModel(
                bank_id=data.bank_id,
                prefix=data.prefix,
                is_active=data.is_active,
            )
        )
        return record

    async def get_by_id(self, id: int) -> CardPrefixModel:
        """Read a record that must exist, including inactive records.

        Args:
            id: Stored record identity.

        Returns:
            The matching stored prefix record.

        Raises:
            NotFoundException: No record has this identity.
        """
        record = await self.repo.get_by_id(id)
        record = self._check_for_id_existence(id, record)
        return record

    async def find_by_id(self, id: int) -> CardPrefixModel | None:
        """Look up a record without requiring its existence.

        Args:
            id: Stored record identity.

        Returns:
            The record, including inactive records; None when absent.
        """
        record = await self.repo.get_by_id(id)
        return record

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CardPrefixModel]:
        """Read matching records with one native ID-set selection.

        Args:
            ids: Bounded trusted record identities.

        Returns:
            Unique matches including inactive records, omitting missing IDs.
            Result order is unspecified; empty input returns no records.
        """
        records = await self.repo.get_by_ids(ids) if ids else []
        return records

    async def get_by_prefix(self, prefix: str) -> CardPrefixModel:
        """Read a record by its exact prefix and require its existence.

        Args:
            prefix: Trusted exact prefix text, including leading zeros.

        Returns:
            The stored prefix record, including inactive records.

        Raises:
            NotFoundException: No record has this prefix.
        """
        record = await self.repo.find_by_prefix(prefix)
        record = self._check_for_existence("prefix", prefix, record)
        return record

    async def find_by_prefix(self, prefix: str) -> CardPrefixModel | None:
        """Look up a record by its unchanged prefix.

        Args:
            prefix: Trusted exact prefix text, including leading zeros.

        Returns:
            The prefix record including inactive records; None when absent.
        """
        record = await self.repo.find_by_prefix(prefix)
        return record

    async def get_by_prefixes(
        self, prefixes: Sequence[str]
    ) -> Sequence[CardPrefixModel]:
        """Read matching records with one native prefix-set selection.

        Args:
            prefixes: Bounded trusted exact prefix strings.

        Returns:
            Unique matches including inactive records; missing values omitted.
            Result order is unspecified; empty input returns no records.
        """
        records = await self.repo.get_by_prefixes(prefixes)
        return records

    async def list(self, query: CardPrefixList) -> PagedType[CardPrefixModel]:
        """List matching records with application-owned pagination.

        Args:
            query: Validated paging, bank and activity filters.

        Returns:
            An ID-ordered page with its filtered total.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            bank_id=query.bank_id,
            is_active=query.is_active,
        )
        return page

    @handle_conflicts(entity="CardPrefix")
    @transactional
    async def update(self, id: int, data: CardPrefixUpdate) -> CardPrefixModel:
        """Apply supplied changes while preserving omitted fields.

        Args:
            id: Stored record identity.
            data: Validated non-null patch fields.

        Returns:
            The updated record, preserving every omitted field.

        Raises:
            NotFoundException: The record identity is absent.
            ValidationException: No recognized update fields were supplied.
            ConflictException: The requested prefix already exists.
        """
        changes = self._check_not_empty_dict(data.to_row())
        record = await self.repo.update_by_id(id, changes)
        record = self._check_for_id_existence(id, record)
        return record

    @transactional
    async def remove(self, id: int) -> CardPrefixModel:
        """Delete a record through the native transaction boundary.

        Args:
            id: Stored record identity.

        Returns:
            The record as stored immediately before deletion.

        Raises:
            NotFoundException: The record identity is absent.
        """
        record = await self.repo.remove_by_id(id)
        record = self._check_for_id_existence(id, record)
        return record
