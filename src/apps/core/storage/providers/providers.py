"""Bind storage connection operations to one native request lifetime."""

from dishka import Provider, Scope, provide

from src.apps.core.storage.providers.app.commands.activity import (
    StorageProviderActivityCommand,
)
from src.apps.core.storage.providers.app.commands.configs import (
    StorageProviderConfigCommand,
)
from src.apps.core.storage.providers.app.commands.create import (
    StorageProviderCreateCommand,
)
from src.apps.core.storage.providers.app.interfaces.commands import (
    IStorageProviderActivityCommand,
    IStorageProviderConfigCommand,
    IStorageProviderCreateCommand,
)
from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderConfigService,
    IStorageProviderService,
)
from src.apps.core.storage.providers.app.services.configs import (
    StorageProviderConfigService,
)
from src.apps.core.storage.providers.app.services.records import (
    StorageProviderService,
)
from src.apps.core.storage.providers.infra.pg.repositories.configs import (
    StorageProviderConfigRepository,
)
from src.apps.core.storage.providers.infra.pg.repositories.records import (
    StorageProviderRepository,
)


class StorageProvider(Provider):
    scope = Scope.REQUEST

    metadata = provide(StorageProviderRepository, scope=Scope.REQUEST)
    configurations = provide(
        StorageProviderConfigRepository, scope=Scope.REQUEST
    )
    metadata_service = provide(
        StorageProviderService,
        provides=IStorageProviderService,
        scope=Scope.REQUEST,
    )
    config_service = provide(
        StorageProviderConfigService,
        provides=IStorageProviderConfigService,
        scope=Scope.REQUEST,
    )
    create_command = provide(
        StorageProviderCreateCommand,
        provides=IStorageProviderCreateCommand,
        scope=Scope.REQUEST,
    )
    config_command = provide(
        StorageProviderConfigCommand,
        provides=IStorageProviderConfigCommand,
        scope=Scope.REQUEST,
    )
    activity_command = provide(
        StorageProviderActivityCommand,
        provides=IStorageProviderActivityCommand,
        scope=Scope.REQUEST,
    )
