"""Resolve payment details for a required identity."""

from papilio.tools.checks import Checks

from ...domain.results.details import PaymentDetail
from ...infra.pg.readers.details import PaymentReader


class PaymentQuery(Checks[PaymentDetail]):
    entity = "Payment"

    def __init__(self, reader: PaymentReader) -> None:
        """Bind the request's payment detail reader."""
        self.reader = reader

    async def get_by_id(self, id: int) -> PaymentDetail:
        """Read one payment with the submitted bank evidence.

        Args:
            id: Stored payment identity.

        Returns:
            The payment and its attached receipt.

        Raises:
            NotFoundException: The payment does not exist.
        """
        detail = await self.reader.get_by_id(id)
        detail = self._check_for_existence("id", id, detail)
        return detail
