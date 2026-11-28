"""Bind webhook key persistence and application operations."""

from dishka import Provider, Scope, provide

from .app.interfaces.services import IAPIKeyService
from .app.services.crud import APIKeyService
from .infra.pg.repositories.crud import APIKeyRepository


class CardAPIKeyProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(APIKeyRepository)
    service = provide(APIKeyService, provides=IAPIKeyService)
