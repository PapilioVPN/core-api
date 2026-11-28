"""Protect registry credentials with native Papilio encryption."""

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt, encrypt
from pydantic import SecretStr

from src.shared.utils.asyncio.threads import ThreadRunner


class NodeCredentialCipher:
    def __init__(
        self, config: CryptoConfig | None, threads: ThreadRunner
    ) -> None:
        key = config.encryption_key if config is not None else ""
        self.key = (
            key
            if key.strip() not in {"", "replace-with-private-encryption-key"}
            else None
        )
        self.threads = threads

    async def seal(self, value: SecretStr) -> str | None:
        """Encrypt the key in a worker, or report unavailable encryption."""
        ciphertext = None
        if self.key is not None:
            ciphertext = await self.threads.run(
                encrypt, value.get_secret_value(), self.key
            )
        return ciphertext

    async def open(self, ciphertext: str) -> SecretStr | None:
        """Recover a credential in a worker or reject unreadable storage."""
        value = None
        if self.key is not None:
            try:
                opened = await self.threads.run(decrypt, ciphertext, self.key)
            except ValueError:
                pass
            else:
                value = SecretStr(opened)
        return value
