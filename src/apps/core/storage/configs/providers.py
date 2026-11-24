"""Bind global storage settings to the native request lifetime."""

from dishka import Provider, Scope, provide

from src.apps.core.storage.configs.app.interfaces.services import (
    IStorageConfigService,
)
from src.apps.core.storage.configs.app.services.storage import (
    StorageConfigService,
)
from src.apps.core.storage.configs.infra.pg.repositories.storage import (
    StorageConfigRepository,
)


class StorageConfigProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(StorageConfigRepository, scope=Scope.REQUEST)
    service = provide(
        StorageConfigService,
        provides=IStorageConfigService,
        scope=Scope.REQUEST,
    )
