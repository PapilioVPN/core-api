"""Public service data for the storefront."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublicService:
    id: int
    title: str
    description: str | None
