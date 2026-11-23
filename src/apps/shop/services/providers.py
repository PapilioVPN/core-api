"""Bind shop service operations to the native request scope."""

from dishka import Provider, Scope, provide

from src.apps.shop.services.app.services.records import Services
from src.apps.shop.services.infra.pg.repositories.records import (
    ServiceRepository,
)


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ServiceRepository)
    services = provide(Services)
