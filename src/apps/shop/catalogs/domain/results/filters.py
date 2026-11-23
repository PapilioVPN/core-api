"""Stable filter choices and price bounds over matching catalog titles."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Choice:
    id: int | str | bool
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class CatalogOptions:
    services: list[Choice]
    statuses: list[Choice]
    volumes: list[Choice]
    expiries: list[Choice]
    min_price: int | None
    max_price: int | None
