"""Catalog profiles and references to reusable sale terms."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, IntType, MStrType, RialType
from pydantic import Field
from pydantic_core import MISSING

from src.apps.shop.catalogs.domain.enums.records import CatalogStatus
from src.apps.shop.durations.domain.dtos.records import DurationCreate
from src.apps.shop.volumes.domain.dtos.records import VolumeCreate

MIN_PRICE = 10_000
Price = Annotated[RialType, Field(ge=MIN_PRICE, strict=True)]
VolumeRef = IdType | VolumeCreate | None
DurationRef = IdType | DurationCreate | None


class CatalogCreate(BaseDTO):
    service_id: IdType
    title: MStrType
    price: Price
    priority: IntType = 0
    status: CatalogStatus = CatalogStatus.DRAFT
    volume: VolumeRef = None
    duration: DurationRef = None


class CatalogProfile(BaseDTO):
    title: MStrType | MISSING = MISSING
    price: Price | MISSING = MISSING
    priority: IntType | MISSING = MISSING
    status: CatalogStatus | MISSING = MISSING


class CatalogUpdate(CatalogProfile):
    volume: VolumeRef | MISSING = MISSING
    duration: DurationRef | MISSING = MISSING


class CatalogPatch(CatalogProfile):
    volume_id: int | None | MISSING = MISSING
    duration_id: int | None | MISSING = MISSING
