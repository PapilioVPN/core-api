"""Save immutable revisions and resolve their exact source for Node calls."""

from papilio.core import resources
from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.dtos.records import XrayRevisionCreate, XrayRevisionList
from ...domain.models.records import XrayRevisionModel
from ...domain.results.records import (
    XrayRevision,
    XrayRevisionSave,
    XrayRevisionSource,
    XraySourceFailure,
)
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

    async def save(
        self, data: XrayRevisionCreate
    ) -> XrayRevisionSave | XraySourceFailure:
        """Register exact proposal bytes without applying them.

        Args:
            data: Validated configuration document as exact UTF-8 bytes.

        Returns:
            Immutable revision metadata or an unavailable result.
        """
        source = data.config_json
        sealed = await self.source_codec.seal(source)
        result: XrayRevisionSave | XraySourceFailure = (
            XraySourceFailure.UNAVAILABLE
        )
        if not isinstance(sealed, XraySourceFailure):
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
        id = await self.repo.insert(record)
        if id is None:
            revision = await self.reader.for_digest(record.config_sha256)
            if revision is None:
                raise RuntimeError("Canonical Xray revision disappeared")
        else:
            revision = XrayRevision(
                id, record.config_sha256, record.size_bytes, record.created_at
            )
        return XrayRevisionSave(revision, created=id is not None)

    async def get_by_id(self, id: int) -> XrayRevision:
        """Read revision metadata or raise for an unknown identity."""
        revision = await self.reader.for_id(id)
        return self._check_for_id_existence(id, revision)

    async def list(self, data: XrayRevisionList) -> PagedType[XrayRevision]:
        """Read one validated page of immutable revision metadata."""
        page = await self.reader.list(
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
        )
        return page

    async def get_source(
        self, id: int
    ) -> XrayRevisionSource | XraySourceFailure:
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
        if isinstance(source, XrayRevisionSource) and (
            len(source.config_json) != stored.size_bytes
            or source.config_sha256 != stored.config_sha256
        ):
            source = XraySourceFailure.UNAVAILABLE
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
