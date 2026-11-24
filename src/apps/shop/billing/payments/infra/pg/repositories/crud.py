"""Native PostgreSQL persistence for payments."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)

from ....domain.models.records import PaymentModel
from ..tables import PaymentTable


class PaymentRepository(PGPersistenceRepository[PaymentModel]):
    table = PaymentTable
