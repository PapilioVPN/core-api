"""Administrator session storage and indexed account listings."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from src.apps.core.access.auth.domain.models.sessions import SessionModel


class SessionTable(SessionModel, BaseTable, table=True):
    table_name = "tbl_admin_sessions"
    __table_args__ = (
        Index("ix_admin_sessions_user_seen", "user_id", "last_seen_at", "id"),
    )
