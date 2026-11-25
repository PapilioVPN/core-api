"""Invalidate the singleton settings read after a committed write."""

from collections.abc import Awaitable, Callable
from functools import wraps
from types import CoroutineType
from typing import Any, Concatenate

from ..interfaces.cache import IPaymentSettingsCacheOwner


class forget_cache:
    @staticmethod
    def one[Owner: IPaymentSettingsCacheOwner, **P, R](
        operation: Callable[Concatenate[Owner, P], Awaitable[R]],
    ) -> Callable[Concatenate[Owner, P], CoroutineType[Any, Any, R]]:
        """Evict the settings view after the operation succeeds."""

        @wraps(operation)
        async def wrapped(self: Owner, *args: P.args, **kwargs: P.kwargs) -> R:
            result = await operation(self, *args, **kwargs)
            await self.cache.forget()
            return result

        return wrapped
