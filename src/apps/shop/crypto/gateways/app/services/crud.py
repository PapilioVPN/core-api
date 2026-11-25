"""Manage sales settings without changing issued crypto payment quotes."""

from collections.abc import Sequence

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import GatewayCreate, GatewayList, GatewayUpdate
from ...domain.models.records import CryptoGatewayModel
from ...infra.pg.repositories.crud import CryptoGatewayRepository


class CryptoGatewayService(IDChecks[CryptoGatewayModel]):
    entity = "CryptoGateway"

    def __init__(self, repo: CryptoGatewayRepository) -> None:
        """Bind gateway persistence to the current request."""
        self.repo = repo

    @handle_conflicts
    @transactional
    async def create(self, data: GatewayCreate) -> CryptoGatewayModel:
        """Register a gateway account and its quote settings.

        Args:
            data: Account details and rials per unit of its pricing currency.

        Returns:
            The saved gateway.

        Raises:
            ConflictException: The account key is already registered.
        """
        gateway = await self.repo.create(
            CryptoGatewayModel.from_dict(data.to_row())
        )
        return gateway

    async def get_by_id(self, id: int) -> CryptoGatewayModel:
        """Read a gateway by identity.

        Args:
            id: Stored gateway identity.

        Returns:
            The matching gateway and its settings.

        Raises:
            NotFoundException: No gateway matches the identity.
        """
        gateway = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, gateway)

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CryptoGatewayModel]:
        """Read a bounded set of gateways.

        Args:
            ids: Stored gateway identities.

        Returns:
            Unique matches, omitting missing gateway identities.
        """
        gateways = await self.repo.get_by_ids(ids) if ids else []
        return gateways

    async def list(self, query: GatewayList) -> PagedType[CryptoGatewayModel]:
        """Read the panel's gateway listings.

        Args:
            query: Validated paging, search and filters.

        Returns:
            The matching page and total.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            kind=query.kind,
            is_active=query.is_active,
        )
        return page

    @transactional
    async def update(self, id: int, data: GatewayUpdate) -> CryptoGatewayModel:
        """Edit sales settings; the account key and kind remain unchanged.

        Args:
            id: Stored gateway identity.
            data: Validated changes. Null payment currency clears the preset.

        Returns:
            The saved gateway with the changes applied.

        Raises:
            ValidationException: No recognized fields were supplied.
            NotFoundException: The gateway does not exist.
            ConflictException: An imported account lacks a provider binding.
        """
        changes = self._check_not_empty_dict(data.to_row())
        if data.is_active is True:
            current = await self.get_by_id(id)
            if current.kind is None:
                raise ConflictException(
                    message="This gateway has no provider configuration.",
                    message_code="crypto_gateway_unconfigured",
                    unique_dict={},
                )
        gateway = await self.repo.update_by_id(id, changes)
        return self._check_for_id_existence(id, gateway)

    @transactional
    async def remove(self, id: int) -> CryptoGatewayModel:
        """Remove a gateway with no payment history.

        Args:
            id: Stored gateway identity.

        Returns:
            The removed gateway.

        Raises:
            NotFoundException: The gateway does not exist.
            ConflictException: A payment references this gateway.
        """
        gateway = await self.repo.remove_by_id(id)
        return self._check_for_id_existence(id, gateway)
