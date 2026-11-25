"""Store crypto payment attempts and read current records."""

from papilio.errors.exceptions import ConflictException
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.dtos.records import CryptoPaymentCreate
from ...domain.enums.records import CryptoPaymentStatus
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import GatewayInvoice
from ...infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentService(IDChecks[CryptoPaymentModel]):
    entity = "CryptoPayment"

    def __init__(self, repo: CryptoPaymentRepository) -> None:
        """Bind the request's crypto payment repository."""
        self.repo = repo

    async def create(self, data: CryptoPaymentCreate) -> CryptoPaymentModel:
        """Store the frozen quote in the caller's transaction."""
        record = await self.repo.create(
            CryptoPaymentModel.from_dict(data.to_row())
        )
        return record

    async def get_by_id(self, id: int) -> CryptoPaymentModel:
        """Read a stored attempt by its internal identity."""
        record = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, record)

    async def get_by_invoice(
        self, gateway_id: int, invoice_id: str
    ) -> CryptoPaymentModel:
        """Resolve one invoice in the scope of the issuing account."""
        record = await self.repo.find_by_invoice(gateway_id, invoice_id)
        return self._check_for_existence("invoice_id", invoice_id, record)

    async def set_invoice(
        self, id: int, invoice: GatewayInvoice
    ) -> CryptoPaymentModel:
        """Attach the invoice once and return the updated attempt."""
        record = await self.repo.set_invoice(
            id, invoice_id=invoice.id, invoice_url=invoice.url
        )
        if record is None:
            raise ConflictException(
                message="The crypto payment can no longer take an invoice.",
                message_code="crypto_invoice_conflict",
                unique_dict={"id": id},
            )
        return record

    async def settle(
        self, id: int, status: CryptoPaymentStatus, provider_payment_id: str
    ) -> CryptoPaymentModel:
        """Apply a verified settlement without reversing a confirmation."""
        pending = (CryptoPaymentStatus.PENDING,)
        states = pending
        confirmed_at = None
        settled_id = None
        if status is CryptoPaymentStatus.CONFIRMED:
            states = (*pending, CryptoPaymentStatus.PARTIAL)
            confirmed_at = utc_now()
            settled_id = provider_payment_id
        record = await self.repo.record_status(
            id,
            states=states,
            status=status,
            provider_payment_id=settled_id,
            confirmed_at=confirmed_at,
        )
        if record is None:
            record = await self.get_by_id(id)
        return record
