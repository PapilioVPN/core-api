"""Evict the detail for a successful catalog record mutation."""

from collections.abc import Awaitable, Callable
from functools import wraps
from types import CoroutineType
from typing import Any, Concatenate

from src.apps.shop.products.catalogs.app.interfaces.cache import (
    ICatalogCacheOwner,
)
from src.apps.shop.products.catalogs.domain.models.records import CatalogModel


class forget_cache:
    @staticmethod
    def one[Owner: ICatalogCacheOwner, **P](
        operation: Callable[Concatenate[Owner, P], Awaitable[CatalogModel]],
    ) -> Callable[
        Concatenate[Owner, P], CoroutineType[Any, Any, CatalogModel]
    ]:
        """Forget the affected ID after the CRUD operation succeeds."""

        @wraps(operation)
        async def wrapped(
            self: Owner, *args: P.args, **kwargs: P.kwargs
        ) -> CatalogModel:
            record = await operation(self, *args, **kwargs)
            await self.cache.forget(record.id)
            return record

        return wrapped
