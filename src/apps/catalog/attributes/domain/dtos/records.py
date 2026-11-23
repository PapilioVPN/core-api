"""Definitions and bounded panel reads for category features."""

from typing import Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    ContentType,
    KeyType,
    MStrType,
    PageType,
    PerPageType,
    ValueType,
)
from pydantic import model_validator
from pydantic_core import MISSING

from src.apps.catalog.attributes.domain.dtos.validators.params import (
    check_param,
)
from src.apps.catalog.attributes.domain.enums.records import (
    AttributeType,
    ParamKey,
)


class AttributeCreate(BaseDTO):
    key: KeyType
    label: MStrType
    type: AttributeType
    description: ContentType | None = None
    param_key: ParamKey | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def check_param_type(self) -> Self:
        check_param(self.type, self.param_key)
        return self


class AttributeUpdate(BaseDTO):
    label: MStrType | MISSING = MISSING
    description: ContentType | None = None
    param_key: ParamKey | None = None
    is_active: bool | MISSING = MISSING


class AttributeList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_active: bool | None = None
