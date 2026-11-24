"""Store and read payment records by identity."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks

from ...domain.models.records import PaymentModel
from ...infra.pg.repositories.crud import PaymentRepository


class PaymentService(IDChecks[PaymentModel]):
    entity = "Payment"

    def __init__(self, repo: PaymentRepository) -> None:
        """Bind the request's payment repository.

        Args:
            repo: Native PostgreSQL payment repository.

        Returns:
            None.
        """
        self.repo = repo

    @transactional
    async def create(self, data: PaymentModel) -> PaymentModel:
        """Persist a prepared pending payment.

        Args:
            data: Payment with its authorized purpose and rial amount.

        Returns:
            The stored payment.
        """
        payment = await self.repo.create(data)
        return payment

    async def get_by_id(self, id: int) -> PaymentModel:
        """Read a payment by identity.

        Args:
            id: Stored payment identity.

        Returns:
            The matching payment.

        Raises:
            NotFoundException: The payment is absent.
        """
        payment = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, payment)

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[PaymentModel]:
        """Read known payment IDs in one native selection.

        Args:
            ids: Bounded list of payment identities.

        Returns:
            Unique matches, omitting missing identities.
        """
        payments = await self.repo.get_by_ids(ids) if ids else []
        return payments
