"""Attribute presentation for the administrative API."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.catalog.attributes.domain.enums.records import (
    AttributeType,
    ParamKey,
)


class AttributeOutput(BaseOutput):
    id: int
    key: str
    label: str
    type: AttributeType
    description: str | None
    param_key: ParamKey | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
