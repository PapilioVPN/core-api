"""Bind attribute definitions and category assignments per request."""

from dishka import Provider, Scope, provide

from src.apps.catalog.attributes.app.services.categories import BindingService
from src.apps.catalog.attributes.app.services.records import AttributeService
from src.apps.catalog.attributes.infra.pg.repositories.categories import (
    BindingRepository,
)
from src.apps.catalog.attributes.infra.pg.repositories.records import (
    AttributeRepository,
)


class AttributeProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(AttributeRepository)
    service = provide(AttributeService)
    bindings = provide(BindingRepository)
    binding_service = provide(BindingService)
