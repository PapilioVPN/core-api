"""Encrypt recoverable Node credentials under the deployment key."""

from typing import Protocol

from pydantic import SecretStr


class INodeCredentialCipher(Protocol):
    async def seal(self, value: SecretStr) -> str | None: ...

    async def open(self, ciphertext: str) -> SecretStr | None: ...
