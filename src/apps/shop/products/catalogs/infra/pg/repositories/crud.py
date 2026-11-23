"""Native PostgreSQL persistence for catalog writes."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)

from src.apps.shop.products.catalogs.domain.models.records import CatalogModel
from src.apps.shop.products.catalogs.infra.pg.tables import CatalogTable


class CatalogRepository(PGPersistenceRepository[CatalogModel]):
    table = CatalogTable
