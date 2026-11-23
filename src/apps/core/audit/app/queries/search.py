"""Panel search over committed audit operations."""

from papilio.schemas.results import PagedType

from src.apps.core.audit.domain.dtos.search import AuditSearch
from src.apps.core.audit.domain.models.records import AuditModel
from src.apps.core.audit.domain.results.filters import AuditOptions
from src.apps.core.audit.infra.pg.readers.search import AuditReader


class AuditQuery:
    def __init__(self, reader: AuditReader) -> None:
        """Bind reads to the current PostgreSQL request.

        Args:
            reader: Audit history and option reader.

        Returns:
            None.
        """
        self.reader = reader

    async def search(self, data: AuditSearch) -> PagedType[AuditModel]:
        """List matching history using the panel's paging controls.

        Args:
            data: Original validated search input.

        Returns:
            Matching audit page and total.
        """
        page = await self.reader.search(
            data,
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
        )
        return page

    async def get_options(self, data: AuditSearch) -> AuditOptions:
        """Show available options across all text matches.

        Args:
            data: Validated search input whose q controls the options.

        Returns:
            Filter counts and time bounds before paging and selections.
        """
        options = await self.reader.get_options(data.q)
        return options
