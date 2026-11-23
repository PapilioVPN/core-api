"""Bind duration operations to Papilio's request scope."""

from dishka import Provider, Scope, provide

from src.apps.shop.durations.app.services.records import Durations
from src.apps.shop.durations.infra.pg.repositories.records import (
    DurationRepository,
)


class DurationsProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(DurationRepository)
    durations = provide(Durations)
