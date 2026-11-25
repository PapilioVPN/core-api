"""Persist cryptocurrency payment records."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)

from ....domain.models.records import CryptoPaymentModel
from ..tables import CryptoPaymentTable


class CryptoPaymentRepository(PGIdentifiedRepository[CryptoPaymentModel]):
    table = CryptoPaymentTable
