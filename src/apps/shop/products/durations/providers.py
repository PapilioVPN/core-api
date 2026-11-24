"""Bind duration operations to Papilio's request scope."""

from dishka import Provider, Scope, provide

from src.apps.shop.products.durations.app.interfaces.services import (
    IDurationService,
)
from src.apps.shop.products.durations.app.services.crud import DurationService
from src.apps.shop.products.durations.infra.pg.repositories.crud import (
    DurationRepository,
)


class DurationsProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(DurationRepository)
    durations = provide(DurationService, provides=IDurationService)
