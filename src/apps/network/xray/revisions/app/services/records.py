"""Save immutable revisions and resolve their exact source for Node calls."""

from papilio.core import resources
from papilio.errors.exceptions import ConflictException, NotFoundException
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from src.shared.utils.order import changed_positions

from ...domain.dtos.records import (
    XrayRevisionBulkRemoveInput,
    XrayRevisionCreate,
    XrayRevisionList,
    XrayRevisionOrderInput,
)
from ...domain.enums.removal import XrayRevisionRemovalStatus
from ...domain.models.records import XrayRevisionModel
from ...domain.results.records import (
    XrayRevision,
    XrayRevisionSave,
    XrayRevisionSource,
)
from ...domain.results.removal import XrayRevisionRemoval
from ..interfaces.records import (
    IXrayRevisionReader,
    IXrayRevisionRepository,
    IXrayRevisionSourceCodec,
)


class XrayRevisionService(IDChecks[XrayRevision]):
    entity = "Xray revision"

    def __init__(
        self,
        repo: IXrayRevisionRepository,
        reader: IXrayRevisionReader,
        source_codec: IXrayRevisionSourceCodec,
    ) -> None:
        """Bind revision persistence, metadata reads and source protection."""
        self.repo = repo
        self.reader = reader
        self.source_codec = source_codec

    async def save(self, data: XrayRevisionCreate) -> XrayRevisionSave | None:
        """Register exact proposal bytes without applying them.

        Args:
            data: Validated configuration document as exact UTF-8 bytes.

        Returns:
            Immutable revision metadata or an unavailable result.
        """
        source = data.config_json
        sealed = await self.source_codec.seal(source)
        result = None
        if sealed is not None:
            result = await self._persist(
                XrayRevisionModel(
                    config_sha256=sealed.config_sha256,
                    size_bytes=len(source),
                    ciphertext=sealed.ciphertext,
                    created_at=utc_now(),
                ),
            )
        return result

    @transactional
    async def _persist(self, record: XrayRevisionModel) -> XrayRevisionSave:
        revision = None
        id = None
        while revision is None:
            id = await self.repo.insert(record)
            if id is None:
                revision = await self.reader.lock_by_digest(
                    record.config_sha256
                )
            else:
                revision = XrayRevision(
                    id,
                    record.config_sha256,
                    record.size_bytes,
                    record.created_at,
                )
        return XrayRevisionSave(revision, created=id is not None)

    async def get_by_id(self, id: int) -> XrayRevision:
        """Read revision metadata or raise for an unknown identity."""
        revision = await self.reader.for_id(id)
        return self._check_for_id_existence(id, revision)

    async def lock_for_reference(self, id: int) -> XrayRevision:
        """Read metadata and hold the revision in the caller's transaction.

        Args:
            id: Stable revision identity to reference in a pending write.

        Returns:
            The revision metadata held until that write commits.

        Raises:
            NotFoundException: The revision is absent.
        """
        revision = await self.reader.lock_for_reference(id)
        return self._check_for_id_existence(id, revision)

    @transactional
    async def remove(self, id: int) -> None:
        """Remove a single unused revision.

        Args:
            id: Stable revision identity.

        Raises:
            NotFoundException: The revision is absent.
            ConflictException: Assignment or execution history references it.
        """
        status = await self.repo.remove_unreferenced_by_id(id)
        if status is XrayRevisionRemovalStatus.NOT_FOUND:
            self._check_for_id_existence(id, None)
        elif status is XrayRevisionRemovalStatus.IN_USE:
            raise ConflictException(
                message="This Xray revision is in use.",
                message_code="xray_revision_in_use",
                unique_dict={},
            )

    @transactional
    async def remove_many(
        self, data: XrayRevisionBulkRemoveInput
    ) -> tuple[XrayRevisionRemoval, ...]:
        """Remove unused revisions from the selection in one transaction.

        Args:
            data: Bounded validated revision identities.

        Returns:
            One outcome per distinct requested ID in first-occurrence order.
        """
        ids = tuple(dict.fromkeys(data.ids))
        results = await self.repo.remove_unreferenced_by_ids(ids)
        return results

    @transactional
    async def reorder(self, data: XrayRevisionOrderInput) -> None:
        """Reassign only the selected revisions' current display positions.

        Args:
            data: Distinct revision IDs in the operator's requested order.

        Raises:
            NotFoundException: A revision is absent and the order is rejected.
        """
        ids = tuple(data.ordered_ids)
        current = await self.repo.lock_sort_positions(ids)
        if len(current) != len(ids):
            missing = next(id for id in ids if id not in current)
            self._check_for_id_existence(missing, None)
        requested = changed_positions(ids, current)
        if requested:
            await self.repo.set_sort_positions(requested)

    async def list(self, data: XrayRevisionList) -> PagedType[XrayRevision]:
        """Read one validated page of immutable revision metadata."""
        page = await self.reader.list(
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
        )
        return page

    async def get_source(self, id: int) -> XrayRevisionSource | None:
        """Load and verify the proposed source before a separate Node call.

        Args:
            id: Stable persisted revision identity.

        Returns:
            The exact source and matching digest, or an unavailable result.

        Raises:
            NotFoundException: The revision does not exist.
        """
        stored = await self._load(id)
        source = await self.source_codec.open(stored.ciphertext)
        if source is not None and (
            len(source.config_json) != stored.size_bytes
            or source.config_sha256 != stored.config_sha256
        ):
            source = None
        return source

    @transactional
    async def _load(self, id: int) -> XrayRevisionModel:
        stored = await self.repo.get_by_id(id)
        if stored is None:
            raise NotFoundException(
                message=f"Cannot find Xray revision with id {id}",
                message_code=resources.NOT_FOUND_ERROR,
                entity=self.entity,
                identifier="id",
                identifier_value=id,
            )
        return stored
