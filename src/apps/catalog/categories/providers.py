"""Bind category operations to a native request scope."""

from dishka import Provider, Scope, alias, provide

from src.apps.catalog.categories.app.interfaces.services import (
    ICategoryService,
)
from src.apps.catalog.categories.app.services.records import CategoryService
from src.apps.catalog.categories.infra.pg.repositories.records import (
    CategoryRepository,
)


class CategoryProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(CategoryRepository)
    service = provide(CategoryService)
    contract = alias(CategoryService, provides=ICategoryService)
