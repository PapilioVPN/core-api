"""Separate commands for operator and authenticated hook intake."""

from typing import Protocol

from ...domain.dtos.records import AdminTransferCreate, HookTransferCreate
from ...domain.models.records import TransferModel


class IAdminTransferCommand(Protocol):
    async def create(
        self, data: AdminTransferCreate, *, admin_id: int
    ) -> TransferModel: ...


class IHookTransferCommand(Protocol):
    async def create(
        self, data: HookTransferCreate, *, key_id: int
    ) -> TransferModel: ...
