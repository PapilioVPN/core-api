"""Bind immutable Xray revisions and their source encryption."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings
from src.shared.utils.asyncio.threads import ThreadRunner

from .app.interfaces.records import (
    IXrayRevisionInboundsQuery,
    IXrayRevisionReader,
    IXrayRevisionRepository,
    IXrayRevisionSelectionQuery,
    IXrayRevisionService,
    IXrayRevisionSourceCodec,
    IXraySourceDigest,
)
from .app.queries.inbounds import XrayRevisionInboundsQuery
from .app.queries.selection import XrayRevisionSelectionQuery
from .app.services.records import XrayRevisionService
from .infra.crypto.digest import XraySourceDigest
from .infra.crypto.source import XrayRevisionSourceCodec
from .infra.pg.readers.records import XrayRevisionReader
from .infra.pg.repositories.records import XrayRevisionRepository


class XrayRevisionsProvider(Provider):
    scope = Scope.REQUEST

    revisions = provide(XrayRevisionService, provides=IXrayRevisionService)
    revision_repo = provide(
        XrayRevisionRepository, provides=IXrayRevisionRepository
    )
    revision_reader = provide(XrayRevisionReader, provides=IXrayRevisionReader)
    selection = provide(
        XrayRevisionSelectionQuery, provides=IXrayRevisionSelectionQuery
    )
    inbounds = provide(
        XrayRevisionInboundsQuery, provides=IXrayRevisionInboundsQuery
    )
    digest = provide(
        XraySourceDigest, provides=IXraySourceDigest, scope=Scope.APP
    )

    @provide(scope=Scope.APP)
    def revision_source(
        self, settings: CoreSettings, threads: ThreadRunner
    ) -> IXrayRevisionSourceCodec:
        """Bind native source processing to the existing key and worker."""
        return XrayRevisionSourceCodec(settings.crypto, threads)
