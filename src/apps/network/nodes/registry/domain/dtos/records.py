"""Validated inputs for the managed node registry."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    IdType,
    IntType,
    MStrType,
    PageType,
    PerPageType,
    ValueType,
)
from pydantic import AfterValidator, Field, SecretStr, StringConstraints
from pydantic_core import MISSING

from .validators.address import normalize_address
from .validators.credentials import validate_api_key, validate_ca_pem

DEFAULT_TIMEOUT = 10

type NodeName = Annotated[MStrType, StringConstraints(strip_whitespace=True)]
type NodeAddress = Annotated[ValueType, AfterValidator(normalize_address)]
type NodePort = Annotated[int, Field(strict=True, ge=1, le=65535)]
type NodeTimeout = Annotated[IntType, Field(strict=True, ge=3)]
type NodeAPIKey = Annotated[SecretStr, AfterValidator(validate_api_key)]
type NodeCA = Annotated[
    str, Field(min_length=1, max_length=65536), AfterValidator(validate_ca_pem)
]


class NodeCreate(BaseDTO):
    name: NodeName
    address: NodeAddress
    port: NodePort
    is_enabled: bool = True
    default_timeout: NodeTimeout = DEFAULT_TIMEOUT
    api_key: NodeAPIKey | None = Field(default=None, repr=False)
    ca_pem: NodeCA | None = Field(default=None, repr=False)


class NodeUpdate(BaseDTO):
    name: NodeName | MISSING = MISSING
    address: NodeAddress | MISSING = MISSING
    port: NodePort | MISSING = MISSING
    is_enabled: bool | MISSING = MISSING
    default_timeout: NodeTimeout | MISSING = MISSING
    api_key: NodeAPIKey | None | MISSING = Field(default=MISSING, repr=False)
    ca_pem: NodeCA | None | MISSING = Field(default=MISSING, repr=False)


class NodeList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_enabled: bool | None = None


class NodeSelectionInput(BaseDTO):
    before_id: IdType | None = None
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_enabled: bool | None = None


class NodeStateInput(BaseDTO):
    node_ids: list[Annotated[IdType, Field(strict=True)]] = Field(
        min_length=1, max_length=100
    )
    is_enabled: Annotated[bool, Field(strict=True)]
