"""Users table with an indexed, required role reference."""

from papilio.infra.db.table import BaseTable

from src.apps.core.users.domain.models.records import UserModel


class UserTable(UserModel, BaseTable, table=True):
    pass
