"""Native PostgreSQL persistence for receipts."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)

from ....domain.models.records import ReceiptModel
from ..tables import ReceiptTable


class ReceiptRepository(PGPersistenceRepository[ReceiptModel]):
    table = ReceiptTable
