"""Validated inputs for the managed node registry."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MStrType, PageType, PerPageType, ValueType
from pydantic import AfterValidator, Field, StringConstraints
from pydantic_core import MISSING

from .validators.address import normalize_address

type NodeName = Annotated[MStrType, StringConstraints(strip_whitespace=True)]
type NodeAddress = Annotated[ValueType, AfterValidator(normalize_address)]
type NodePort = Annotated[int, Field(strict=True, ge=1, le=65535)]


class NodeCreate(BaseDTO):
    name: NodeName
    address: NodeAddress
    port: NodePort
    is_enabled: bool = True


class NodeUpdate(BaseDTO):
    name: NodeName | MISSING = MISSING
    address: NodeAddress | MISSING = MISSING
    port: NodePort | MISSING = MISSING
    is_enabled: bool | MISSING = MISSING


class NodeList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_enabled: bool | None = None
