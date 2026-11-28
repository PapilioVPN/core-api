"""Bind card transfer settings and their panel cache."""

from dishka import Provider, Scope, provide

from .app.interfaces.cache import ITransferSettingsCache
from .app.interfaces.queries import ITransferSettingsQuery
from .app.interfaces.services import ITransferSettingsService
from .app.queries.records import TransferSettingsQuery
from .app.services.crud import TransferSettingsService
from .infra.pg.repositories.crud import TransferSettingsRepository
from .infra.redis.repositories.records import TransferSettingsCache


class TransferSettingsProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(TransferSettingsRepository)
    cache = provide(
        TransferSettingsCache, scope=Scope.APP, provides=ITransferSettingsCache
    )
    service = provide(
        TransferSettingsService, provides=ITransferSettingsService
    )
    query = provide(TransferSettingsQuery, provides=ITransferSettingsQuery)
