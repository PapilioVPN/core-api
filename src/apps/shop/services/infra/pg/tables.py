"""Shop service storage discovered by Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from src.apps.shop.services.domain.models.records import ServiceModel


class ServiceTable(ServiceModel, BaseTable, table=True):
    __table_args__ = (Index("ix_services_priority", "priority", "id"),)
