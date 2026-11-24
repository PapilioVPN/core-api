"""Persist and read completed OCR attempts."""

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.types.constants import INT64_MAX

from ...domain.dtos.records import OCRRequestList
from ...domain.models.records import OCRRequestModel
from ...infra.pg.repositories.crud import OCRRequestRepository


class OCRRequestService(IDChecks[OCRRequestModel]):
    entity = "OCRRequest"

    def __init__(self, repo: OCRRequestRepository) -> None:
        """Bind the request's native OCR repository."""
        self.repo = repo

    @transactional
    async def create(self, data: OCRRequestModel) -> OCRRequestModel | None:
        """Register a completed attempt in the caller's transaction if open.

        Args:
            data: Prepared attempt with its receipt and delivery identities.

        Returns:
            The stored attempt, or None when the event already has a record.
        """
        record = await self.repo.insert(data)
        return record

    async def exists_by_event(self, event_id: str) -> bool:
        """Check whether a delivered event has already been recorded.

        Args:
            event_id: Stable identity carried by the delivered event.

        Returns:
            Whether the event has a stored attempt.
        """
        exists = await self.repo.exists_by_event(event_id)
        return exists

    async def get_by_id(self, id: int) -> OCRRequestModel:
        """Read one attempt by its stored identity.

        Args:
            id: Stored OCR attempt identity.

        Returns:
            The matching attempt.

        Raises:
            NotFoundException: No attempt has this identity.
        """
        record = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, record)

    async def find_by_event(self, event_id: str) -> OCRRequestModel | None:
        """Read one attempt by its originating event.

        Args:
            event_id: Stable identity carried by the delivered event.

        Returns:
            The matching attempt, or None when the event has no record.
        """
        record = await self.repo.find_by_event(event_id)
        return record

    async def list(self, query: OCRRequestList) -> PagedType[OCRRequestModel]:
        """Page completed attempts in descending identity order.

        Args:
            query: Native paging and optional receipt and outcome filters.

        Returns:
            The selected page and its total matching count.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=min((query.page - 1) * query.per_page, INT64_MAX),
            receipt_id=query.receipt_id,
            status=query.status,
        )
        return page
