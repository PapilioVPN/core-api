"""Validated starter definitions for the catalog seeds."""

from src.apps.catalog.attributes.domain.dtos.records import AttributeCreate
from src.apps.catalog.attributes.domain.enums.records import (
    AttributeType,
    ParamKey,
)
from src.apps.catalog.categories.domain.dtos.records import CategoryCreate
from src.apps.core.scopes.domain.dtos.records import ScopeCreate

SUBSCRIPTIONS = CategoryCreate(slug="subscriptions", title="Subscriptions")
CATEGORIES = (SUBSCRIPTIONS,)
SCOPES = (ScopeCreate(key="catalog", title="Catalog"),)
ATTRIBUTES = (
    AttributeCreate(
        key="duration_days",
        label="Duration (days)",
        type=AttributeType.INT,
        param_key=ParamKey.DURATION_DAYS,
    ),
    AttributeCreate(
        key="quota_bytes",
        label="Quota (bytes)",
        type=AttributeType.INT,
        param_key=ParamKey.QUOTA_BYTES,
    ),
)
