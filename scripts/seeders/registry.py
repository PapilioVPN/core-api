"""Explicit seed registration; dependencies precede their consumers."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial

from papilio.infra.db.uow import PGUnitOfWork

from scripts.seeders.catalog.attributes import seed_attributes
from scripts.seeders.catalog.bindings import seed_bindings
from scripts.seeders.catalog.categories import seed_categories
from scripts.seeders.catalog.data import (
    ATTRIBUTES,
    CATEGORIES,
    SCOPES,
    SUBSCRIPTIONS,
)
from scripts.seeders.catalog.scopes import seed_scopes


@dataclass(frozen=True, slots=True)
class Seed:
    key: str
    execute: Callable[[PGUnitOfWork], Awaitable[int]]
    requires: tuple[str, ...] = ()


def registered_seeds() -> tuple[Seed, ...]:
    """Validate offline data and bind explicit module inputs."""
    return (
        Seed("catalog.scopes", partial(seed_scopes, scopes=SCOPES)),
        Seed(
            "catalog.categories",
            partial(seed_categories, categories=CATEGORIES),
        ),
        Seed(
            "catalog.attributes",
            partial(seed_attributes, attributes=ATTRIBUTES),
        ),
        Seed(
            "catalog.bindings",
            partial(
                seed_bindings,
                slug=SUBSCRIPTIONS.slug,
                keys=tuple(attribute.key for attribute in ATTRIBUTES),
            ),
            requires=("catalog.categories", "catalog.attributes"),
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
    selected: set[str] = set()
    if not targets:
        return seeds
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
    return tuple(seed for seed in seeds if seed.key in selected)
