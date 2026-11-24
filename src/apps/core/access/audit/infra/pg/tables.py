"""Audit timeline and filtered history indexes."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from src.apps.core.access.audit.domain.models.records import AuditModel


class AuditTable(AuditModel, BaseTable, table=True):
    table_name = "tbl_audit_records"
    __table_args__ = (
        Index("ix_audit_created", "created_at", "id"),
        Index("ix_audit_actor_created", "actor_id", "created_at", "id"),
        Index("ix_audit_action_created", "action", "created_at", "id"),
    )
