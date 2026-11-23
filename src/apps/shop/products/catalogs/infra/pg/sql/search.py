"""SQL selections for catalog search and text-scoped filter counts."""

from sqlalchemy import Select, func, or_, select
from sqlmodel import col

from src.apps.shop.products.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.products.catalogs.domain.enums.records import CatalogSort
from src.apps.shop.products.catalogs.infra.pg.tables import CatalogTable
from src.apps.shop.products.services.infra.pg.tables import ServiceTable


def _matching(q: str | None) -> Select[tuple[CatalogTable]]:
    table = CatalogTable
    stmt = select(table).join(
        ServiceTable, col(ServiceTable.id) == col(table.service_id)
    )
    if q is not None:
        stmt = stmt.where(
            or_(
                col(table.title).icontains(q, autoescape=True),
                col(ServiceTable.title).icontains(q, autoescape=True),
            )
        )
    return stmt


def search(data: CatalogSearch) -> Select[tuple[CatalogTable]]:
    """Select a page source with all chosen filters and stable ordering."""
    table = CatalogTable
    stmt = _matching(data.q)
    if data.service_id is not None:
        stmt = stmt.where(col(table.service_id) == data.service_id)
    if data.status is not None:
        stmt = stmt.where(col(table.status) == data.status)
    if data.volume_id is not None:
        stmt = stmt.where(col(table.volume_id) == data.volume_id)
    if data.is_unlimited is not None:
        stmt = stmt.where(col(table.volume_id).is_(None) == data.is_unlimited)
    if data.duration_id is not None:
        stmt = stmt.where(col(table.duration_id) == data.duration_id)
    if data.has_expiry is not None:
        stmt = stmt.where(
            col(table.duration_id).is_not(None) == data.has_expiry
        )
    if data.min_price is not None:
        stmt = stmt.where(col(table.price) >= data.min_price)
    if data.max_price is not None:
        stmt = stmt.where(col(table.price) <= data.max_price)

    order = {
        CatalogSort.PRIORITY: col(table.priority),
        CatalogSort.TITLE: col(table.title),
        CatalogSort.PRICE: col(table.price),
        CatalogSort.CREATED_AT: col(table.created_at),
    }[data.sort_by]
    sort = order.desc() if data.sort_order.value == "desc" else order.asc()
    return stmt.order_by(sort, col(table.id))


def facets(q: str | None) -> Select:
    """Aggregate the text matches before selected filters or pagination."""
    table = CatalogTable
    grouped = (
        col(table.service_id),
        col(ServiceTable.title),
        col(table.status),
        col(table.volume_id).is_(None),
        col(table.duration_id).is_not(None),
    )
    stmt = _matching(q).with_only_columns(
        *grouped,
        func.count(),
        func.min(col(table.price)),
        func.max(col(table.price)),
        maintain_column_froms=True,
    )
    return stmt.group_by(*grouped)
