"""Forget the changed record after a successful config replacement."""

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
from typing import Any, Concatenate

from ...domain.models.configs import ConfigModel
from ..interfaces.cache import ICacheOwner


class forget_cache:
    @staticmethod
    def one[Owner: ICacheOwner, **P](
        operation: Callable[Concatenate[Owner, P], Awaitable[ConfigModel]],
    ) -> Callable[Concatenate[Owner, P], Coroutine[Any, Any, ConfigModel]]:
        @wraps(operation)
        async def wrapped(
            self: Owner, *args: P.args, **kwargs: P.kwargs
        ) -> ConfigModel:
            config = await operation(self, *args, **kwargs)
            await self.cache.forget(config.key)
            return config

        return wrapped
