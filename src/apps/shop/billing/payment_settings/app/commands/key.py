"""Issue a new payment hook key without retaining its plaintext."""

from secrets import token_urlsafe

from papilio.security.crypto import hash_sha256

from ..interfaces.services import IPaymentSettingsService


class PaymentKeyCommand:
    def __init__(self, settings: IPaymentSettingsService) -> None:
        """Bind the record service that persists the prepared key digest."""
        self.settings = settings

    async def issue(self) -> str:
        """Store a new key digest and return the plaintext key once."""
        key = token_urlsafe(32)
        await self.settings.set_key_hash(hash_sha256(key))
        return key
