"""Own wallet top-up requests and their customer-scoped reads."""

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.types.constants import INT64_MAX

from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)

from ...domain.dtos.records import DepositCreate, DepositSearch
from ...domain.models.records import WalletDepositModel
from ...infra.pg.repositories.crud import WalletDepositRepository


class WalletDepositService(IDChecks[WalletDepositModel]):
    entity = "WalletDeposit"

    def __init__(
        self, repo: WalletDepositRepository, customers: ICustomerService
    ) -> None:
        """Bind the request's deposit repository and customer service."""
        self.repo = repo
        self.customers = customers

    @transactional
    async def create(
        self, customer_id: int, data: DepositCreate
    ) -> WalletDepositModel:
        """Record a request to top up an existing customer's wallet.

        Args:
            customer_id: Identity of the customer requesting the top-up.
            data: Validated positive amount in whole rials.

        Returns:
            The stored request with its ID and creation time.

        Raises:
            NotFoundException: The customer is absent.
        """
        await self.customers.get_by_id(customer_id)
        row = await self.repo.create(
            WalletDepositModel(customer_id=customer_id, amount=data.amount)
        )
        return row

    async def get_by_id(self, customer_id: int, id: int) -> WalletDepositModel:
        """Read one of the customer's requests.

        Args:
            customer_id: Owning customer identity.
            id: Stored deposit request identity.

        Returns:
            The stored top-up request.

        Raises:
            NotFoundException: The request is absent under this customer.
        """
        row = await self.repo.get(customer_id, id)
        return self._check_for_id_existence(id, row)

    async def search(
        self, customer_id: int, data: DepositSearch
    ) -> PagedType[WalletDepositModel]:
        """Read a bounded page of the customer's requests.

        Args:
            customer_id: Owning customer identity.
            data: Validated page and optional amount filter in whole rials.

        Returns:
            The matching page and its total count.
        """
        page = await self.repo.search(
            customer_id,
            amount=data.amount,
            limit=data.per_page,
            offset=min((data.page - 1) * data.per_page, INT64_MAX),
        )
        return page
