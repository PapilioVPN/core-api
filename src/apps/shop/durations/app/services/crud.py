"""Create and read reusable duration definitions."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.shop.durations.domain.dtos.records import (
    DurationCreate,
    DurationList,
)
from src.apps.shop.durations.domain.models.records import DurationModel
from src.apps.shop.durations.infra.pg.repositories.crud import (
    DurationRepository,
)


class DurationCRUD(IDChecks[DurationModel]):
    entity = "Duration"

    def __init__(self, repo: DurationRepository) -> None:
        """Bind the request's duration repository."""
        self.repo = repo

    @transactional
    async def create(self, data: DurationCreate) -> DurationModel:
        """Register one validity rule.

        Args:
            data: Validated period in days and the event that starts it.

        Returns:
            The stored duration with its identity and creation time.
        """
        duration = await self.repo.insert(
            DurationModel(days=data.days, starts_on=data.starts_on)
        )
        if duration is None:
            duration = await self.repo.find_by_terms(data.days, data.starts_on)
        duration = self._check_for_existence("days", data.days, duration)
        return duration

    async def get_by_id(self, id: int) -> DurationModel:
        """Read a duration definition by its stable identity.

        Args:
            id: Stored duration identity.

        Returns:
            The stored validity rule.

        Raises:
            NotFoundException: The identity is absent.
        """
        duration = await self.find_by_id(id)
        duration = self._check_for_id_existence(id, duration)
        return duration

    async def find_by_id(self, id: int) -> DurationModel | None:
        """Read a stored identity, returning None if it is absent."""
        duration = await self.repo.get_by_id(id)
        return duration

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[DurationModel]:
        """Read a bounded set in one query, omitting absent identities."""
        rows = await self.repo.get_by_ids(ids) if ids else []
        return rows

    async def list(self, query: DurationList) -> PagedType[DurationModel]:
        """Read definitions for the panel's duration picker.

        Args:
            query: Validated paging bounds.

        Returns:
            The selected page in ID order and the total number of definitions.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            days=query.days,
            min_days=query.min_days,
            max_days=query.max_days,
        )
        return page
