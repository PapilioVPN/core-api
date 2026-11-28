"""Issue, read, revoke and verify the card transfer webhook keys."""

from secrets import token_urlsafe

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.security.crypto import hash_sha256
from papilio.tools.checks import IDChecks
from papilio.types.constants import INT64_MAX
from papilio.utils.dates import utc_now

from ...domain.dtos.records import APIKeyCreate, APIKeyList
from ...domain.models.records import APIKeyModel
from ...domain.results.issued import IssuedAPIKey
from ...infra.pg.repositories.crud import APIKeyRepository


class APIKeyService(IDChecks[APIKeyModel]):
    entity = "CardAPIKey"

    def __init__(self, repo: APIKeyRepository) -> None:
        self.repo = repo

    @transactional
    async def create(self, data: APIKeyCreate) -> IssuedAPIKey:
        """Generate a random key, persisting only its digest and metadata.

        Args:
            data: Panel title and timezone-aware expiration.

        Returns:
            Created metadata and the plaintext key for one-time disclosure.

        Raises:
            ValidationException: The requested expiration is not in the future.
        """
        if data.expires_at <= utc_now():
            raise ValidationException(
                message="API key expiration must be in the future.",
                message_code="card_api_key_expiry_invalid",
                loc=["expires_at"],
            )
        key = f"ctc_{token_urlsafe(32)}"
        record = await self.repo.create(
            APIKeyModel(
                title=data.title,
                prefix=key[:12],
                digest=hash_sha256(key),
                expires_at=data.expires_at,
            )
        )
        return IssuedAPIKey(api_key=record, key=key)

    async def list(self, data: APIKeyList) -> PagedType[APIKeyModel]:
        """List the newest keys first, including expired and revoked keys.

        Args:
            data: Validated page number and size.

        Returns:
            One page of stored records and the unpaged count.
        """
        page = await self.repo.list(
            limit=data.per_page,
            offset=min((data.page - 1) * data.per_page, INT64_MAX),
        )
        return page

    async def get_by_id(self, id: int) -> APIKeyModel:
        """Read one key record for the panel.

        Args:
            id: Stored key identity.

        Returns:
            The stored record, including expired and revoked keys.

        Raises:
            NotFoundException: The key does not exist.
        """
        record = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, record)

    @transactional
    async def revoke(self, id: int) -> APIKeyModel:
        """Revoke an issued key once, retaining its original revocation time.

        Args:
            id: Stored key identity.

        Returns:
            The revoked key record.

        Raises:
            NotFoundException: The key does not exist.
        """
        record = await self.repo.revoke(id, revoked_at=utc_now())
        if record is None:
            record = await self.get_by_id(id)
        return record

    async def verify(self, key: str) -> int | None:
        """Resolve a valid card transfer credential from PostgreSQL.

        Args:
            key: The exact opaque value received at the hook boundary.

        Returns:
            The key identity, or None for unknown, expired or revoked keys.
        """
        record = await self.repo.find_active(hash_sha256(key), now=utc_now())
        return record.id if record is not None else None
