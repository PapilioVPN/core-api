"""Shared execution adapters; AnyIO owns worker pools and shutdown."""

from dishka import Provider, Scope, provide

from src.shared.utils.asyncio.threads import ThreadRunner


class AsyncioProvider(Provider):
    @provide(scope=Scope.APP)
    def threads(self) -> ThreadRunner:
        """Bind one adapter using AnyIO's native thread defaults.

        Args:
            None.

        Returns:
            Shared runner without request-owned resources.
        """
        return ThreadRunner()
