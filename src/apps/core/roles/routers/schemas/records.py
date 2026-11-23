"""Explicit role and composed permission HTTP outputs."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class RoleOutput(BaseOutput):
    id: int
    key: str
    title: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ScopePermissionOutput(BaseOutput):
    scope_id: int
    key: str
    title: str
    is_active: bool
    permissions: int


class RoleDetailsOutput(RoleOutput):
    scopes: list[ScopePermissionOutput]
