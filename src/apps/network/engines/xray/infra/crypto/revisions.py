"""Protect revision source with the existing Papilio deployment key."""

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt, encrypt

from ...domain.exceptions.revisions import XrayRevisionSourceUnavailable


class XrayRevisionCipher:
    def __init__(self, config: CryptoConfig | None) -> None:
        """Bind the deployment's existing authenticated-encryption settings."""
        self.config = config

    def _key(self) -> str:
        key = self.config.encryption_key if self.config is not None else ""
        if not key.strip() or key == "replace-with-private-encryption-key":
            raise XrayRevisionSourceUnavailable()
        return key

    def seal(self, source: bytes) -> str:
        """Encrypt exact UTF-8 JSON bytes with the native Papilio cipher."""
        return encrypt(source.decode("utf-8"), self._key())

    def open(self, ciphertext: str) -> bytes:
        """Recover the exact source, hiding native decryption diagnostics."""
        key = self._key()
        try:
            source = decrypt(ciphertext, key).encode("utf-8")
        except ValueError as error:
            raise XrayRevisionSourceUnavailable() from error
        return source
