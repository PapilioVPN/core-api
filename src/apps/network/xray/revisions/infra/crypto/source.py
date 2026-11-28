"""Protect revision source with the existing Papilio deployment key."""

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt, encrypt

from src.shared.utils.asyncio.threads import ThreadRunner

from ...domain.results.records import (
    XrayRevisionSource,
    XraySealedSource,
    XraySourceFailure,
)
from .digest import digest_hex

_SAMPLE_KEY = "replace-with-private-encryption-key"


def _seal(source: bytes, key: str) -> XraySealedSource:
    digest = digest_hex(source)
    ciphertext = encrypt(source.decode("utf-8"), key)
    return XraySealedSource(digest, ciphertext)


def _open(ciphertext: str, key: str) -> XrayRevisionSource | XraySourceFailure:
    try:
        source = decrypt(ciphertext, key).encode("utf-8")
    except ValueError:
        result = XraySourceFailure.UNAVAILABLE
    else:
        result = XrayRevisionSource(digest_hex(source), source)
    return result


class XrayRevisionSourceCodec:
    def __init__(
        self, config: CryptoConfig | None, threads: ThreadRunner
    ) -> None:
        """Bind deployment encryption and the native worker runner."""
        self.config = config
        self.threads = threads

    def _key(self) -> str | None:
        key = self.config.encryption_key if self.config is not None else ""
        return key if key.strip() and key != _SAMPLE_KEY else None

    async def seal(
        self, source: bytes
    ) -> XraySealedSource | XraySourceFailure:
        """Encrypt and hash the exact source in one worker call.

        Args:
            source: Exact validated UTF-8 configuration bytes.

        Returns:
            Encrypted source and its digest, or an unavailable result.

        """
        key = self._key()
        sealed = XraySourceFailure.UNAVAILABLE
        if key is not None:
            sealed = await self.threads.run(_seal, source, key)
        return sealed

    async def open(
        self, ciphertext: str
    ) -> XrayRevisionSource | XraySourceFailure:
        """Recover and hash the exact source in one worker call.

        Args:
            ciphertext: Authenticated ciphertext stored with the revision.

        Returns:
            The decrypted bytes and digest, or an unavailable result.

        """
        key = self._key()
        source = XraySourceFailure.UNAVAILABLE
        if key is not None:
            source = await self.threads.run(_open, ciphertext, key)
        return source
