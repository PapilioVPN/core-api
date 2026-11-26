"""Bind the Xray engine capability to the native container."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings

from .app.commands.start import XrayStartCommand
from .app.executions.start import XrayStartExecution
from .app.interfaces.revisions import (
    IXrayRevisionCipher,
    IXrayRevisionReader,
    IXrayRevisionRepository,
    IXrayRevisionService,
)
from .app.interfaces.start import (
    IXrayStartCommand,
    IXrayStartGateway,
    IXrayStartQuery,
    IXrayStartRepository,
)
from .app.interfaces.status import IXrayStatusGateway, IXrayStatusQuery
from .app.interfaces.validation import (
    IXrayConfigGateway,
    IXrayConfigValidation,
)
from .app.pipelines.start import XrayStartPipeline
from .app.queries.start import XrayStartQuery
from .app.queries.status import XrayStatusQuery
from .app.services.revisions import XrayRevisionService
from .app.services.validation import XrayConfigValidationService
from .infra.crypto.revisions import XrayRevisionCipher
from .infra.grpc.start import XrayStartGateway
from .infra.grpc.status import XrayStatusGateway
from .infra.grpc.validation import XrayConfigGateway
from .infra.pg.readers.revisions import XrayRevisionReader
from .infra.pg.repositories.revisions import XrayRevisionRepository
from .infra.pg.repositories.start import XrayStartRepository


class XrayProvider(Provider):
    scope = Scope.REQUEST

    gateway = provide(
        XrayConfigGateway, provides=IXrayConfigGateway, scope=Scope.APP
    )
    validation = provide(
        XrayConfigValidationService, provides=IXrayConfigValidation
    )
    status_gateway = provide(
        XrayStatusGateway, provides=IXrayStatusGateway, scope=Scope.APP
    )
    status = provide(XrayStatusQuery, provides=IXrayStatusQuery)
    revisions = provide(XrayRevisionService, provides=IXrayRevisionService)
    revision_repo = provide(
        XrayRevisionRepository, provides=IXrayRevisionRepository
    )
    revision_reader = provide(XrayRevisionReader, provides=IXrayRevisionReader)
    start_command = provide(XrayStartCommand, provides=IXrayStartCommand)
    start_query = provide(XrayStartQuery, provides=IXrayStartQuery)
    start_repo = provide(XrayStartRepository, provides=IXrayStartRepository)
    start_gateway = provide(
        XrayStartGateway, provides=IXrayStartGateway, scope=Scope.APP
    )
    start_execution = provide(XrayStartExecution, scope=Scope.APP)
    start_pipeline = provide(XrayStartPipeline, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def revision_cipher(self, settings: CoreSettings) -> IXrayRevisionCipher:
        """Bind native encryption with the existing deployment key."""
        return XrayRevisionCipher(settings.crypto)
