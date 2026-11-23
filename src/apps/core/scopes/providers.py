"""Bind scope persistence and its app contract to one native request."""

from dishka import Provider, Scope, provide

from src.apps.core.scopes.app.interfaces.services import IScopeService
from src.apps.core.scopes.app.services.crud import ScopeService
from src.apps.core.scopes.infra.pg.repositories.crud import (
    ScopeRepository,
)


class ScopeProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(ScopeRepository)
    service = provide(ScopeService, provides=IScopeService)
