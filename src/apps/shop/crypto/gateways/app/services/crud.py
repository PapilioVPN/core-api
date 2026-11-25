"""Manage cryptocurrency gateway accounts."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import GatewayCreate, GatewayList, GatewayUpdate
from ...domain.models.records import CryptoGatewayModel
from ...infra.pg.repositories.crud import CryptoGatewayRepository
from ..decorators.configs import forget_cache
from ..interfaces.cache import IGatewayConfigCache


class CryptoGatewayService(IDChecks[CryptoGatewayModel]):
    entity = "CryptoGateway"

    def __init__(
        self, repo: CryptoGatewayRepository, cache: IGatewayConfigCache
    ) -> None:
        """Bind the repository and the cache invalidated on deletion."""
        self.repo = repo
        self.cache = cache

    @transactional
    async def create(self, data: GatewayCreate) -> CryptoGatewayModel:
        """Register an account.

        Args:
            data: Validated provider kind and account metadata.

        Returns:
            The stored account and its generated identity.
        """
        gateway = await self.repo.create(
            CryptoGatewayModel.from_dict(data.to_row())
        )
        return gateway

    async def get_by_id(self, id: int) -> CryptoGatewayModel:
        """Read the account by identity.

        Args:
            id: Stored account identity.

        Returns:
            The matching account, including inactive accounts.

        Raises:
            NotFoundException: The account does not exist.
        """
        gateway = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, gateway)

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CryptoGatewayModel]:
        """Read a bounded account set.

        Args:
            ids: Requested account identities.

        Returns:
            Distinct accounts, with missing identities omitted.
        """
        gateways = await self.repo.get_by_ids(ids) if ids else []
        return gateways

    async def list(self, query: GatewayList) -> PagedType[CryptoGatewayModel]:
        """Read a filtered gateway page.

        Args:
            query: Validated page, title, provider and activity filters.

        Returns:
            The requested account page and its filtered total.
        """
        gateways = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            kind=query.kind,
            is_active=query.is_active,
        )
        return gateways

    @transactional
    async def update(self, id: int, data: GatewayUpdate) -> CryptoGatewayModel:
        """Edit the account metadata without changing its provider.

        Args:
            id: Stored account identity.
            data: Validated patch. Omitted fields stay unchanged.

        Returns:
            The updated account.

        Raises:
            NotFoundException: The account does not exist.
            ValidationException: No recognized changes were supplied.
        """
        changes = self._check_not_empty_dict(data.to_row())
        gateway = await self.repo.update_by_id(id, changes)
        return self._check_for_id_existence(id, gateway)

    @forget_cache.one
    @transactional
    async def remove(self, id: int) -> CryptoGatewayModel:
        """Remove an unused account and its stored connection settings.

        Args:
            id: Stored account identity.

        Returns:
            The removed account.

        Raises:
            NotFoundException: The account does not exist.
            ConflictException: A payment references the account.
        """
        gateway = await self.repo.remove_by_id(id)
        return self._check_for_id_existence(id, gateway)
