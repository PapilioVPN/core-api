"""Coordinate catalog writes that resolve service and sale definitions."""

from papilio.infra.db.tools.decorators import transactional
from pydantic_core import MISSING

from src.apps.shop.products.catalogs.app.interfaces.services import (
    ICatalogService,
    ICatalogTermsService,
)
from src.apps.shop.products.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogPatch,
    CatalogUpdate,
)
from src.apps.shop.products.catalogs.domain.models.records import CatalogModel
from src.apps.shop.products.services.app.interfaces.services import (
    IShopService,
)


class CatalogCreateCommand:
    def __init__(
        self,
        catalogs: ICatalogService,
        services: IShopService,
        terms: ICatalogTermsService,
    ) -> None:
        """Bind catalog records, services and sale terms to the request."""
        self.catalogs = catalogs
        self.services = services
        self.terms = terms

    @transactional
    async def create(self, data: CatalogCreate) -> CatalogModel:
        """Register a catalog and resolve its terms in one transaction.

        Args:
            data: Validated service, fixed rial price, and optional terms.

        Returns:
            The stored catalog with the resolved term identities.

        Raises:
            NotFoundException: A selected service or term is absent.
        """
        await self.services.get_by_id(data.service_id)
        volume_id = await self.terms.volume_id(data.volume)
        duration_id = await self.terms.duration_id(data.duration)
        catalog = await self.catalogs.create(
            CatalogModel(
                service_id=data.service_id,
                title=data.title,
                price=data.price,
                priority=data.priority,
                status=data.status,
                volume_id=volume_id,
                duration_id=duration_id,
            )
        )
        return catalog


class CatalogUpdateCommand:
    def __init__(
        self, catalogs: ICatalogService, terms: ICatalogTermsService
    ) -> None:
        """Bind catalog records and sale terms to the request."""
        self.catalogs = catalogs
        self.terms = terms

    @transactional
    async def update(self, id: int, data: CatalogUpdate) -> CatalogModel:
        """Apply a profile patch and its resolved terms atomically.

        Args:
            id: Stored catalog identity.
            data: Original patch. Null clears a supplied term reference.

        Returns:
            Updated catalog, preserving every omitted field.

        Raises:
            NotFoundException: The catalog or a selected term is absent.
            ValidationException: The patch has no recognized changes.
        """
        volume_id = MISSING
        if data.volume is not MISSING:
            volume_id = await self.terms.volume_id(data.volume)
        duration_id = MISSING
        if data.duration is not MISSING:
            duration_id = await self.terms.duration_id(data.duration)
        patch = CatalogPatch.model_construct(
            title=data.title,
            price=data.price,
            priority=data.priority,
            status=data.status,
            volume_id=volume_id,
            duration_id=duration_id,
        )
        catalog = await self.catalogs.update(id, patch)
        return catalog
