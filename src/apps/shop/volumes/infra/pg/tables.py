"""Volume table discovered by Papilio."""

from papilio.infra.db.table import BaseTable

from src.apps.shop.volumes.domain.models.records import VolumeModel


class VolumeTable(VolumeModel, BaseTable, table=True):
    pass
