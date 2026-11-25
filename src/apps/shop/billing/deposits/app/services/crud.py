"""Store and read bank deposit records."""

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import DepositSearch
from ...domain.models.records import DepositModel
from ...infra.pg.repositories.crud import DepositRepository


class DepositService(IDChecks[DepositModel]):
    entity = "Deposit"

    def __init__(self, repo: DepositRepository) -> None:
        """Bind the request's native deposit repository."""
        self.repo = repo

    @transactional
    async def create(self, data: DepositModel) -> DepositModel:
        """Persist an authorized bank report and any payment it confirmed."""
        record = await self.repo.create(data)
        return record

    async def link(self, id: int, payment_id: int) -> DepositModel:
        """Return the deposit after linking its confirmed payment."""
        record = await self.repo.update_by_id(id, {"payment_id": payment_id})
        return self._check_for_id_existence(id, record)

    async def get(self, id: int) -> DepositModel:
        """Return the bank report with the given stored identity."""
        record = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, record)

    async def search(self, query: DepositSearch) -> PagedType[DepositModel]:
        """Return a bounded page of matching bank reports."""
        page = await self.repo.search(query)
        return page
