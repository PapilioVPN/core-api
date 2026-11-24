"""Native PostgreSQL record operations for customer profiles."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)

from ....domain.models.records import CustomerModel
from ..tables import CustomerTable


class CustomerRepository(PGPersistenceRepository[CustomerModel]):
    table = CustomerTable
