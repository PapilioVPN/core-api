"""Native PostgreSQL persistence for duration definitions."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)

from src.apps.shop.durations.domain.models.records import DurationModel
from src.apps.shop.durations.infra.pg.tables import DurationTable


class DurationRepository(PGIdentifiedRepository[DurationModel]):
    table = DurationTable
