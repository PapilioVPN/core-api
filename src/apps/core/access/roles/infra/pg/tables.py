"""Roles and their unique scope assignments."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import UniqueConstraint
from sqlmodel import Relationship

from src.apps.core.access.roles.domain.models.records import (
    RoleModel,
    RoleScopeModel,
)
from src.apps.core.access.scopes.infra.pg.tables import ScopeTable


class RoleTable(RoleModel, BaseTable, table=True):
    scope_assignments: list["RoleScopeTable"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={
            "lazy": "raise",
            "order_by": "RoleScopeTable.scope_id",
            "passive_deletes": "all",
        },
    )


class RoleScopeTable(RoleScopeModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint(
            "role_id", "scope_id", name="uq_role_scopes_role_id_scope_id"
        ),
    )
    role: RoleTable = Relationship(
        back_populates="scope_assignments",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    scope: ScopeTable = Relationship(sa_relationship_kwargs={"lazy": "raise"})
