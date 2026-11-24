"""Explicit seed registration; dependencies precede their consumers."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial

from papilio.infra.db.uow import PGUnitOfWork

from scripts.seeders.banking.banks import seed_banks
from scripts.seeders.banking.card_prefixes import seed_card_prefixes
from scripts.seeders.banking.data import load_banking


@dataclass(frozen=True, slots=True)
class Seed:
    key: str
    execute: Callable[[PGUnitOfWork], Awaitable[int]]
    requires: tuple[str, ...] = ()


def registered_seeds() -> tuple[Seed, ...]:
    """Validate offline data and bind explicit module inputs."""
    banking = load_banking()
    return (
        Seed(
            "banking.banks",
            partial(seed_banks, banks=banking.banks),
        ),
        Seed(
            "banking.card_prefixes",
            partial(seed_card_prefixes, banks=banking.banks),
            requires=("banking.banks",),
        ),
    )


def select_seeds(
    seeds: tuple[Seed, ...], targets: list[str]
) -> tuple[Seed, ...]:
    """Select all, groups or module keys, including ordered prerequisites.

    Args:
        seeds: Explicit registry ordered with dependencies first.
        targets: Group/module keys; an empty list means all registered seeds.

    Returns:
        Unique seeds in registry order, with all prerequisites included.

    Raises:
        ValueError: A target is unknown or registration order is invalid.
    """
    seen: set[str] = set()
    for seed in seeds:
        if seed.key in seen or not set(seed.requires) <= seen:
            raise ValueError(f"Invalid seed registration order: {seed.key}")
        seen.add(seed.key)
    result = seeds
    if targets:
        selected: set[str] = set()
        for target in targets:
            matches = {
                seed.key
                for seed in seeds
                if seed.key == target or seed.key.startswith(target + ".")
            }
            if not matches:
                raise ValueError(f"Unknown seed target: {target}")
            selected.update(matches)
        for seed in reversed(seeds):
            if seed.key in selected:
                selected.update(seed.requires)
        result = tuple(seed for seed in seeds if seed.key in selected)
    return result
