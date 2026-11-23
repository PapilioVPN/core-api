"""Bind catalog commands, queries and cache in native scopes."""

from dishka import Provider, Scope, provide

from src.apps.shop.catalogs.app.commands.records import CatalogCommand
from src.apps.shop.catalogs.app.interfaces.commands import ICatalogCommand
from src.apps.shop.catalogs.app.interfaces.queries import ICatalogQuery
from src.apps.shop.catalogs.app.queries.panel import CatalogQuery
from src.apps.shop.catalogs.infra.pg.readers.panel import CatalogReader
from src.apps.shop.catalogs.infra.pg.repositories.records import (
    CatalogRepository,
)
from src.apps.shop.catalogs.infra.redis.repositories.details import (
    CatalogCache,
)


class CatalogProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CatalogRepository)
    reader = provide(CatalogReader)
    cache = provide(CatalogCache, scope=Scope.APP)
    command = provide(CatalogCommand, provides=ICatalogCommand)
    query = provide(CatalogQuery, provides=ICatalogQuery)
