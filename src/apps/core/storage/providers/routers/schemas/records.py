"""Connection creation input and credential-free metadata output."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput
from pydantic import Field

from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderCreate,
)


class StorageProviderCreateInput(StorageProviderCreate):
    config: S3Config | None = Field(default=None, repr=False)


class StorageProviderOutput(BaseOutput):
    id: int
    key: str
    title: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
