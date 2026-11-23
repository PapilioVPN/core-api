"""Bind catalog services, commands, queries and cache."""

from dishka import Provider, Scope, provide

from src.apps.shop.products.catalogs.app.commands.records import CatalogCommand
from src.apps.shop.products.catalogs.app.interfaces.cache import ICatalogCache
from src.apps.shop.products.catalogs.app.interfaces.commands import (
    ICatalogCommand,
)
from src.apps.shop.products.catalogs.app.interfaces.public import (
    IPublicCatalogQuery,
    IServiceCatalogQuery,
)
from src.apps.shop.products.catalogs.app.interfaces.queries import (
    ICatalogFormQuery,
    ICatalogQuery,
    ICatalogSearchQuery,
)
from src.apps.shop.products.catalogs.app.interfaces.services import (
    ICatalogCRUD,
)
from src.apps.shop.products.catalogs.app.queries.form import CatalogFormQuery
from src.apps.shop.products.catalogs.app.queries.public import (
    PublicCatalogQuery,
)
from src.apps.shop.products.catalogs.app.queries.records import CatalogQuery
from src.apps.shop.products.catalogs.app.queries.search import (
    CatalogSearchQuery,
)
from src.apps.shop.products.catalogs.app.queries.service import (
    ServiceCatalogQuery,
)
from src.apps.shop.products.catalogs.app.services.crud import CatalogCRUD
from src.apps.shop.products.catalogs.infra.pg.readers.details import (
    CatalogReader,
)
from src.apps.shop.products.catalogs.infra.pg.readers.public import (
    PublicCatalogReader,
)
from src.apps.shop.products.catalogs.infra.pg.readers.search import (
    CatalogSearchReader,
)
from src.apps.shop.products.catalogs.infra.pg.readers.service import (
    ServiceCatalogReader,
)
from src.apps.shop.products.catalogs.infra.pg.repositories.crud import (
    CatalogRepository,
)
from src.apps.shop.products.catalogs.infra.redis.repositories.details import (
    CatalogCache,
)


class CatalogProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CatalogRepository)
    reader = provide(CatalogReader)
    search_reader = provide(CatalogSearchReader)
    cache = provide(CatalogCache, scope=Scope.APP, provides=ICatalogCache)
    crud = provide(CatalogCRUD, provides=ICatalogCRUD)
    command = provide(CatalogCommand, provides=ICatalogCommand)
    query = provide(CatalogQuery, provides=ICatalogQuery)
    search = provide(CatalogSearchQuery, provides=ICatalogSearchQuery)
    form = provide(CatalogFormQuery, provides=ICatalogFormQuery)
    public_reader = provide(PublicCatalogReader)
    public = provide(PublicCatalogQuery, provides=IPublicCatalogQuery)
    service_reader = provide(ServiceCatalogReader)
    service = provide(ServiceCatalogQuery, provides=IServiceCatalogQuery)
