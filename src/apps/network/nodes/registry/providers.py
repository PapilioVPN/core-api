"""Bind Node registry persistence, selection and operator state."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings
from src.shared.utils.asyncio.threads import ThreadRunner

from .app.commands.state import NodeStateCommand
from .app.interfaces.credentials import INodeCredentialCipher
from .app.interfaces.endpoints import INodeEndpointQuery, INodeEndpointReader
from .app.interfaces.repositories import INodeRepository
from .app.interfaces.selection import INodeSelectionQuery, INodeSelectionReader
from .app.interfaces.services import INodeService
from .app.interfaces.state import INodeStateCommand
from .app.queries.endpoints import NodeEndpointQuery
from .app.queries.selection import NodeSelectionQuery
from .app.services.crud import NodeService
from .infra.crypto.credentials import NodeCredentialCipher
from .infra.pg.readers.endpoints import NodeEndpointReader
from .infra.pg.readers.selection import NodeSelectionReader
from .infra.pg.repositories.crud import NodeRepository


class NodeRegistryProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(NodeRepository, provides=INodeRepository)
    nodes = provide(NodeService, provides=INodeService)
    endpoints = provide(NodeEndpointQuery, provides=INodeEndpointQuery)
    endpoint_reader = provide(NodeEndpointReader, provides=INodeEndpointReader)
    selection = provide(NodeSelectionQuery, provides=INodeSelectionQuery)
    selection_reader = provide(
        NodeSelectionReader, provides=INodeSelectionReader
    )
    state = provide(NodeStateCommand, provides=INodeStateCommand)

    @provide(scope=Scope.APP)
    def credentials(
        self, settings: CoreSettings, threads: ThreadRunner
    ) -> INodeCredentialCipher:
        """Bind the native deployment key and its shared worker runner."""
        return NodeCredentialCipher(settings.crypto, threads)
