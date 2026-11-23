"""Bind shop service operations to the native request scope."""

from dishka import Provider, Scope, provide

from src.apps.shop.products.services.app.interfaces.public import (
    IPublicServiceQuery,
)
from src.apps.shop.products.services.app.interfaces.services import (
    IServiceCRUD,
)
from src.apps.shop.products.services.app.queries.public import (
    PublicServiceQuery,
)
from src.apps.shop.products.services.app.services.crud import ServiceCRUD
from src.apps.shop.products.services.infra.pg.readers.public import (
    PublicServiceReader,
)
from src.apps.shop.products.services.infra.pg.repositories.crud import (
    ServiceRepository,
)


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ServiceRepository)
    services = provide(ServiceCRUD, provides=IServiceCRUD)
    public_reader = provide(PublicServiceReader)
    public = provide(PublicServiceQuery, provides=IPublicServiceQuery)
