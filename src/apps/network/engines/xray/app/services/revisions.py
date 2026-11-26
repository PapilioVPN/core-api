"""Save immutable revisions and resolve their exact source for Node calls."""

from hashlib import sha256

from papilio.core import resources
from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.dtos.revisions import XrayRevisionCreate, XrayRevisionList
from ...domain.exceptions.revisions import XrayRevisionSourceUnavailable
from ...domain.models.revisions import XrayRevisionModel
from ...domain.results.revisions import (
    XrayRevision,
    XrayRevisionSave,
    XrayRevisionSource,
)
from ..interfaces.revisions import (
    IXrayRevisionCipher,
    IXrayRevisionReader,
    IXrayRevisionRepository,
)


class XrayRevisionService(IDChecks[XrayRevision]):
    entity = "Xray revision"

    def __init__(
        self,
        repo: IXrayRevisionRepository,
        reader: IXrayRevisionReader,
        cipher: IXrayRevisionCipher,
    ) -> None:
        """Bind revision persistence, metadata reads and source protection."""
        self.repo = repo
        self.reader = reader
        self.cipher = cipher

    @transactional
    async def save(self, data: XrayRevisionCreate) -> XrayRevisionSave:
        """Register exact proposal bytes without applying them.

        Args:
            data: Validated configuration document as exact UTF-8 bytes.

        Returns:
            The immutable revision metadata and whether it was inserted.

        Raises:
            XrayRevisionSourceUnavailable: No usable encryption key exists.
        """
        source = data.config_json
        digest = sha256(source).hexdigest()
        created_at = utc_now()
        size = len(source)
        id = await self.repo.insert(
            XrayRevisionModel(
                config_sha256=digest,
                size_bytes=size,
                ciphertext=self.cipher.seal(source),
                created_at=created_at,
            )
        )
        if id is None:
            revision = await self.reader.for_digest(digest)
            if revision is None:
                raise RuntimeError("Canonical Xray revision disappeared")
        else:
            revision = XrayRevision(id, digest, size, created_at)
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

    @transactional
    async def get_source(self, id: int) -> XrayRevisionSource:
        """Load and verify the proposed source before a separate Node call.

        Args:
            id: Stable persisted revision identity.

        Returns:
            The exact original bytes and matching digest.

        Raises:
            NotFoundException: The revision does not exist.
            XrayRevisionSourceUnavailable: The source cannot be recovered.
        """
        stored = await self.repo.get_by_id(id)
        if stored is None:
            raise NotFoundException(
                message=f"Cannot find Xray revision with id {id}",
                message_code=resources.NOT_FOUND_ERROR,
                entity=self.entity,
                identifier="id",
                identifier_value=id,
            )
        source = self.cipher.open(stored.ciphertext)
        if (
            len(source) != stored.size_bytes
            or sha256(source).hexdigest() != stored.config_sha256
        ):
            raise XrayRevisionSourceUnavailable()
        return XrayRevisionSource(stored.config_sha256, source)
