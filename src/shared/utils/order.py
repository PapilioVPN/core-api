"""Reassign existing display positions in the requested record order."""


def require_distinct_ids(ids: list[int]) -> list[int]:
    """Reject repeated IDs before any ordering write."""
    if len(ids) != len(set(ids)):
        raise ValueError("ordered_ids must not contain duplicates")
    return ids


def changed_positions(
    ordered_ids: tuple[int, ...], current: dict[int, int]
) -> dict[int, int]:
    """Return only selected records that move to a different position."""
    return {
        id: position
        for id, position in zip(
            ordered_ids, sorted(current.values()), strict=True
        )
        if current[id] != position
    }
