"""Evict the panel projection after an owning gateway mutation."""

from collections.abc import Awaitable, Callable
from functools import wraps
from types import CoroutineType
from typing import Any, Concatenate

from ..interfaces.cache import IGatewayConfigCacheOwner


class forget_cache:
    @staticmethod
    def one[Owner: IGatewayConfigCacheOwner, **P, R](
        operation: Callable[Concatenate[Owner, int, P], Awaitable[R]],
    ) -> Callable[Concatenate[Owner, int, P], CoroutineType[Any, Any, R]]:
        """Forget the affected gateway after the operation returns."""

        @wraps(operation)
        async def wrapped(
            self: Owner, id: int, /, *args: P.args, **kwargs: P.kwargs
        ) -> R:
            result = await operation(self, id, *args, **kwargs)
            await self.cache.forget(id)
            return result

        return wrapped
