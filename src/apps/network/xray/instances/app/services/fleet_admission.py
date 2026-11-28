"""Reserve Xray lifecycle slots with native PostgreSQL set operations."""

from datetime import datetime

from papilio.utils.dates import utc_now

from src.apps.network.nodes.app.interfaces.endpoints import INodeEndpointQuery

from ...domain.dtos.identity import XrayExecutionRequestKey
from ...domain.enums.fleet import XrayFleetOperationStatus
from ...domain.enums.start import XrayExecutionAction
from ...domain.models.start import XrayStartModel
from ...domain.results.fleet import (
    XrayFleetOperationResult,
    XrayFleetReservation,
)
from ..interfaces.start import IXrayStartRepository


def _index(
    records: tuple[XrayStartModel, ...],
) -> dict[XrayExecutionRequestKey, XrayStartModel]:
    return {
        (row.node_id, row.instance_id, row.request_key): row for row in records
    }


def _result(
    key: XrayExecutionRequestKey,
    record: XrayStartModel | None,
    rejection: XrayFleetOperationStatus,
    *,
    action: XrayExecutionAction,
    revision_id: int | None,
    now: datetime,
) -> XrayFleetOperationResult:
    node_id, instance_id, _ = key
    if record is None:
        result = XrayFleetOperationResult(node_id, instance_id, rejection)
    elif record.action is not action or record.revision_id != revision_id:
        result = XrayFleetOperationResult(
            node_id, instance_id, XrayFleetOperationStatus.REQUEST_CONFLICT
        )
    else:
        result = XrayFleetOperationResult(
            node_id,
            instance_id,
            XrayFleetOperationStatus.ACCEPTED,
            record.observed_at(now),
            record.id,
        )
    return result


class XrayFleetAdmission:
    def __init__(
        self, nodes: INodeEndpointQuery, repo: IXrayStartRepository
    ) -> None:
        self.nodes = nodes
        self.repo = repo

    async def reserve(
        self,
        keys: tuple[XrayExecutionRequestKey, ...],
        *,
        action: XrayExecutionAction,
        revision_id: int | None,
    ) -> XrayFleetReservation:
        """Reserve distinct scoped requests in the command's transaction.

        Args:
            keys: Bounded identities in operator selection order.
            action: Lifecycle action assigned by the calling command.
            revision_id: Saved source ID, or None for a source-free action.

        Returns:
            Per-target decisions and only newly inserted IDs for publication.
        """
        records = _index(await self.repo.find_requests(keys))
        pending = tuple(sorted(key for key in keys if key not in records))
        rejections: dict[
            XrayExecutionRequestKey, XrayFleetOperationStatus
        ] = {}
        inserted: tuple[XrayStartModel, ...] = ()
        if pending:
            endpoints = await self.nodes.get_endpoints(
                tuple(dict.fromkeys(key[0] for key in pending))
            )
            candidates: list[XrayStartModel] = []
            for key in pending:
                node_id, instance_id, request_key = key
                endpoint = endpoints.get(node_id)
                if endpoint is None:
                    rejections[key] = XrayFleetOperationStatus.NODE_NOT_FOUND
                elif not endpoint.is_enabled:
                    rejections[key] = XrayFleetOperationStatus.NODE_DISABLED
                else:
                    candidates.append(
                        XrayStartModel(
                            node_id=node_id,
                            instance_id=instance_id,
                            request_key=request_key,
                            address=endpoint.address,
                            port=endpoint.port,
                            action=action,
                            revision_id=revision_id,
                        )
                    )
            if candidates:
                await self.repo.expire_many(
                    tuple(
                        (row.node_id, row.instance_id) for row in candidates
                    ),
                    utc_now(),
                )
                inserted = await self.repo.insert_many(tuple(candidates))
                records.update(_index(inserted))
                # Read after ON CONFLICT to distinguish a concurrent replay
                # from a different request that owns the active slot.
                unresolved = tuple(
                    key
                    for key in pending
                    if key not in rejections and key not in records
                )
                if unresolved:
                    records.update(
                        _index(await self.repo.find_requests(unresolved))
                    )
        now = utc_now()
        results = tuple(
            _result(
                key,
                records.get(key),
                rejections.get(key, XrayFleetOperationStatus.ACTIVE_OPERATION),
                action=action,
                revision_id=revision_id,
                now=now,
            )
            for key in keys
        )
        return XrayFleetReservation(results, tuple(row.id for row in inserted))
