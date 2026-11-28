"""Seal routing inputs and verify replay identity on a worker thread."""

from hashlib import sha256

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt, encrypt

from src.shared.utils.asyncio.threads import ThreadRunner

from ...domain.dtos.mutations import RoutingIntent, intent_adapter
from ...domain.enums.operation import RoutingPayloadFailure
from ...domain.results.operation import RoutingPayload


def _seal(intent: RoutingIntent, key: str) -> RoutingPayload:
    data = intent_adapter.dump_json(intent)
    return RoutingPayload(
        sha256(data).hexdigest(), encrypt(data.decode(), key)
    )


def _open(
    payload: RoutingPayload, key: str
) -> RoutingIntent | RoutingPayloadFailure:
    result: RoutingIntent | RoutingPayloadFailure = (
        RoutingPayloadFailure.UNAVAILABLE
    )
    try:
        data = decrypt(payload.ciphertext, key).encode()
        if sha256(data).hexdigest() == payload.digest:
            result = intent_adapter.validate_json(data)
    except ValueError:
        pass
    return result


class RoutingPayloadCodec:
    def __init__(
        self, config: CryptoConfig | None, threads: ThreadRunner
    ) -> None:
        key = config.encryption_key if config is not None else ""
        self.key = (
            key
            if key.strip() and key != "replace-with-private-encryption-key"
            else None
        )
        self.threads = threads

    async def seal(
        self, intent: RoutingIntent
    ) -> RoutingPayload | RoutingPayloadFailure:
        """Encrypt and fingerprint the typed request before SQL admission.

        Args:
            intent: Validated payload for one routing action.

        Returns:
            Sealed intent or its protection failure.
        """
        result: RoutingPayload | RoutingPayloadFailure = (
            RoutingPayloadFailure.UNAVAILABLE
        )
        if self.key is not None:
            result = await self.threads.run(_seal, intent, self.key)
        return result

    async def open(
        self, payload: RoutingPayload
    ) -> RoutingIntent | RoutingPayloadFailure:
        """Recover a validated intent whose fingerprint matches storage.

        Args:
            payload: Bound encrypted payload and its recorded fingerprint.

        Returns:
            Verified intent or its protection failure.
        """
        result: RoutingIntent | RoutingPayloadFailure = (
            RoutingPayloadFailure.UNAVAILABLE
        )
        if self.key is not None:
            result = await self.threads.run(_open, payload, self.key)
        return result
