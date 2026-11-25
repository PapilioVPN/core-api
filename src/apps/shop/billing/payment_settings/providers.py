"""Bind the request-scoped payment settings service."""

from dishka import Provider, Scope, provide

from .app.interfaces.cache import IPaymentSettingsCache
from .app.interfaces.queries import IPaymentSettingsQuery
from .app.interfaces.services import IPaymentSettingsService
from .app.queries.records import PaymentSettingsQuery
from .app.services.crud import PaymentSettingsService
from .infra.pg.repositories.crud import PaymentSettingsRepository
from .infra.redis.repositories.records import PaymentSettingsCache


class PaymentSettingsProvider(Provider):
    scope = Scope.REQUEST

    cache = provide(
        PaymentSettingsCache, scope=Scope.APP, provides=IPaymentSettingsCache
    )
    query = provide(PaymentSettingsQuery, provides=IPaymentSettingsQuery)
    repo = provide(PaymentSettingsRepository)
    settings = provide(
        PaymentSettingsService, provides=IPaymentSettingsService
    )
