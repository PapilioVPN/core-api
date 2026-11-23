"""Bind catalog CRUD, queries and cache in native scopes."""

from dishka import Provider, Scope, provide

from src.apps.shop.catalogs.app.interfaces.queries import ICatalogQuery
from src.apps.shop.catalogs.app.interfaces.services import ICatalogCRUD
from src.apps.shop.catalogs.app.queries.panel import CatalogQuery
from src.apps.shop.catalogs.app.services.crud import CatalogCRUD
from src.apps.shop.catalogs.infra.pg.readers.panel import CatalogReader
from src.apps.shop.catalogs.infra.pg.repositories.crud import (
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
    crud = provide(CatalogCRUD, provides=ICatalogCRUD)
    query = provide(CatalogQuery, provides=ICatalogQuery)
