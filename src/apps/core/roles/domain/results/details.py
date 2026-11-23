"""Materialized role and scope-permission read results."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RoleAccess:
    id: int
    is_active: bool
    scopes: dict[str, int]


@dataclass(frozen=True, slots=True)
class ScopePermissionResult:
    scope_id: int
    key: str
    title: str
    is_active: bool
    permissions: int


@dataclass(frozen=True, slots=True)
class RoleDetailsResult:
    id: int
    key: str
    title: str
    description: str | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
    scopes: list[ScopePermissionResult]
