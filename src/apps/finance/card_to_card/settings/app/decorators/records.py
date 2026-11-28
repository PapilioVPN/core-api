"""Forget the changed record after a successful settings write."""

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
from typing import Any, Concatenate

from ...domain.models.records import TransferSettingsModel
from ..interfaces.cache import ITransferSettingsCacheOwner


class forget_cache:
    @staticmethod
    def one[Owner: ITransferSettingsCacheOwner, **P](
        operation: Callable[
            Concatenate[Owner, P], Awaitable[TransferSettingsModel]
        ],
    ) -> Callable[
        Concatenate[Owner, P], Coroutine[Any, Any, TransferSettingsModel]
    ]:
        @wraps(operation)
        async def wrapped(
            self: Owner, *args: P.args, **kwargs: P.kwargs
        ) -> TransferSettingsModel:
            settings = await operation(self, *args, **kwargs)
            await self.cache.forget(settings.key)
            return settings

        return wrapped
