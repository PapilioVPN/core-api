"""Hash the exact candidate bytes through the shared thread runner."""

from hashlib import sha256

from src.shared.utils.asyncio.threads import ThreadRunner


def digest_hex(source: bytes) -> str:
    """Compute the lowercase SHA-256 of the exact source bytes."""
    return sha256(source).hexdigest()


class XraySourceDigest:
    def __init__(self, threads: ThreadRunner) -> None:
        self.threads = threads

    async def digest(self, source: bytes) -> str:
        """Compute the proposal digest without blocking the event loop.

        Args:
            source: Exact configuration bytes validated at the entrypoint.

        Returns:
            Lowercase hexadecimal SHA-256 of the source.
        """
        result = await self.threads.run(digest_hex, source)
        return result
