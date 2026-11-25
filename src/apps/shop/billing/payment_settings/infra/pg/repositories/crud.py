"""Native PostgreSQL access to payment settings."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)

from ....domain.models.records import PaymentSettingsModel
from ..tables import PaymentSettingsTable


class PaymentSettingsRepository(PGPersistenceRepository[PaymentSettingsModel]):
    table = PaymentSettingsTable
