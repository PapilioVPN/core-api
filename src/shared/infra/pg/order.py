"""Build the PostgreSQL statements used by both ordered catalogs."""

from sqlalchemy import (
    BigInteger,
    ColumnElement,
    Select,
    any_,
    bindparam,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped
from sqlalchemy.sql.selectable import TableValuedAlias


def display_position(
    sort_order: Mapped[int | None], id: Mapped[int]
) -> ColumnElement[int]:
    """Give untouched records unique positions in newest-first order."""
    return func.coalesce(sort_order, -id)


def cursor_position(
    sort_order: Mapped[int | None], id: Mapped[int], before_id: int
) -> ColumnElement[int]:
    """Resolve an ID cursor's position with its default as a fallback."""
    anchor = (
        select(display_position(sort_order, id))
        .where(id == before_id)
        .scalar_subquery()
    )
    return func.coalesce(anchor, -before_id)


def lock_display_positions(
    sort_order: Mapped[int | None], id: Mapped[int], ids: tuple[int, ...]
) -> Select[tuple[int, int]]:
    """Lock selected rows in stable ID order and project their positions."""
    selected = bindparam("order_ids", ids, type_=ARRAY(BigInteger))
    return (
        select(id, display_position(sort_order, id))
        .where(id == any_(selected))
        .order_by(id)
        .with_for_update(key_share=True)
    )


def display_position_changes(positions: dict[int, int]) -> TableValuedAlias:
    """Bind changed records and positions as rows from two arrays."""
    ids = bindparam("position_ids", tuple(positions), type_=ARRAY(BigInteger))
    slots = bindparam(
        "sort_positions", tuple(positions.values()), type_=ARRAY(BigInteger)
    )
    return (
        func.unnest(ids, slots)
        .table_valued("id", "sort_position")
        .render_derived()
    )
