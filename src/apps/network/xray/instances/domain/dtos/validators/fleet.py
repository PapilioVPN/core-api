"""Validate unique target identities in a fleet mutation selection."""

from ..identity import XrayInstanceTarget


def require_distinct_targets[T: XrayInstanceTarget](
    targets: list[T], *, selection: str
) -> list[T]:
    if len({(row.node_id, row.instance_id) for row in targets}) != len(
        targets
    ):
        raise ValueError(f"An instance may appear only once in {selection}")
    return targets
