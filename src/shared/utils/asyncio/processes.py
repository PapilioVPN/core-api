"""Typed CPU execution through AnyIO's native worker processes."""

from collections.abc import Callable
from functools import partial

from anyio import CapacityLimiter, to_process


class ProcessRunner:
    """Bind native concurrency and cancellation options for Python CPU work."""

    def __init__(
        self,
        *,
        limiter: CapacityLimiter | None = None,
        cancellable: bool = False,
    ) -> None:
        """Configure native worker options without creating a pool.

        Args:
            limiter: Shared native limiter, or None for AnyIO's default.
            cancellable: Kill a running worker when its call is cancelled.

        Returns:
            None.
        """
        self.limiter = limiter
        self.cancellable = cancellable

    async def run[**P, R](
        self, function: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs
    ) -> R:
        """Run synchronous CPU work in a separate native worker process.

        Args:
            function: Importable callable, without closures or lambdas.
            *args: Pickleable positional arguments, without live resources.
            **kwargs: Pickleable keyword arguments, without live resources.

        Returns:
            The pickleable result, with its declared type preserved.

        Raises:
            Exception: Native worker or callable errors propagate unchanged.

        Running calls are shielded by default. With cancellable=True, native
        cancellation kills the worker; use this for disposable computation.
        A supplied limiter bounds workers; None uses AnyIO's default limiter.
        """
        call = partial(function, *args, **kwargs)
        result = await to_process.run_sync(
            call, cancellable=self.cancellable, limiter=self.limiter
        )
        return result
