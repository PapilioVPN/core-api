"""Bind the receipt image service to private local storage."""

from pathlib import Path

from anyio import Path as AsyncPath
from dishka import Provider, Scope, provide
from papilio.core.config import StorageConfig

from .app.interfaces.images import IReceiptImages
from .app.services.images import ReceiptImages
from .infra.local import ReceiptFiles


class ReceiptProvider(Provider):
    scope = Scope.APP

    images = provide(ReceiptImages, provides=IReceiptImages)

    @provide
    async def files(self, config: StorageConfig) -> ReceiptFiles:
        """Resolve a private sibling of the existing media directory.

        Args:
            config: Shared Storage paths, including its staging directory.

        Returns:
            The private adapter without a separate receipt setting.

        Raises:
            ValueError: A media or staging path would expose receipt bytes.
        """
        public = await AsyncPath(config.path).resolve()
        root = await public.with_name(f"{public.name}-private").resolve()
        staging = await AsyncPath(config.temp_dir).resolve()
        if (
            root.is_relative_to(public)
            or public.is_relative_to(root)
            or staging.is_relative_to(public)
        ):
            raise ValueError("Receipt storage must be outside public media")
        await root.mkdir(mode=0o700, parents=True, exist_ok=True)
        return ReceiptFiles(Path(root))
