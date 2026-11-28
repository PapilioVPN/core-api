"""Correlated decisions and operation evidence for fleet mutations."""

from dataclasses import dataclass

from ..enums.fleet import XrayFleetOperationStatus
from ..models.start import XrayStartModel


@dataclass(frozen=True, slots=True)
class XrayFleetOperationResult:
    node_id: int
    instance_id: str
    status: XrayFleetOperationStatus
    operation: XrayStartModel | None = None
    operation_id: int | None = None


@dataclass(frozen=True, slots=True)
class XrayFleetReservation:
    results: tuple[XrayFleetOperationResult, ...]
    inserted_ids: tuple[int, ...]
