"""Typed blocking-I/O execution through AnyIO's native worker threads."""

from collections.abc import Callable
from functools import partial

from anyio import CapacityLimiter, to_thread


class ThreadRunner:
    """Bind native concurrency and cancellation options for blocking I/O."""

    def __init__(
        self,
        *,
        limiter: CapacityLimiter | None = None,
        abandon_on_cancel: bool = False,
    ) -> None:
        """Configure native worker options without creating a pool.

        Args:
            limiter: Shared native limiter, or None for AnyIO's default.
            abandon_on_cancel: Stop waiting on cancellation; work continues.

        Returns:
            None.
        """
        self.limiter = limiter
        self.abandon_on_cancel = abandon_on_cancel

    async def run[**P, R](
        self, function: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs
    ) -> R:
        """Run synchronous blocking I/O outside the event-loop thread.

        Args:
            function: Synchronous callable without loop-bound clients/sessions.
            *args: Positional arguments passed unchanged to the callable.
            **kwargs: Keyword arguments passed unchanged to the callable.

        Returns:
            The callable's result, with its declared type preserved.

        Raises:
            Exception: Native worker or callable errors propagate unchanged.

        Cancellation follows AnyIO: by default wait for the running thread;
        abandoning stops waiting and releases capacity but leaves work running.
        A limiter bounds awaited calls, including calls from other runners
        sharing it; None uses AnyIO's default limiter.
        """
        call = partial(function, *args, **kwargs)
        result = await to_thread.run_sync(
            call,
            abandon_on_cancel=self.abandon_on_cancel,
            limiter=self.limiter,
        )
        return result
