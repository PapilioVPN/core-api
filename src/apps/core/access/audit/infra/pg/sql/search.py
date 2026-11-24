"""Shared audit search predicates for hits and filter counts."""

from papilio.types.constants import INT64_MAX
from papilio.types.enums import SortOrder
from sqlalchemy import ColumnElement, Select, asc, desc, or_, select, true
from sqlmodel import col

from src.apps.core.access.audit.domain.dtos.search import AuditSearch
from src.apps.core.access.audit.domain.enums.actions import AuditAction
from src.apps.core.access.audit.domain.enums.sorts import AuditSortBy
from src.apps.core.access.audit.infra.pg.tables import AuditTable


def match(q: str | None) -> ColumnElement[bool]:
    """Build a literal match over action labels and recorded identities.

    Args:
        q: Optional search text. Numeric IDs must fit a PostgreSQL bigint.

    Returns:
        A bound SQL predicate shared by history and facet reads.
    """
    condition: ColumnElement[bool] = true()
    if q is not None:
        clauses = [
            col(AuditTable.action).icontains(q, autoescape=True),
            col(AuditTable.target_id).icontains(q, autoescape=True),
        ]
        text = q.casefold()
        labels = [
            action.value
            for action in AuditAction
            if text in action.fa.casefold()
        ]
        if labels:
            clauses.append(col(AuditTable.action).in_(labels))
        if len(q) <= 19 and q.isdecimal() and (id := int(q)) <= INT64_MAX:
            clauses.extend(
                (
                    col(AuditTable.id) == id,
                    col(AuditTable.actor_id) == id,
                    col(AuditTable.role_id) == id,
                    col(AuditTable.scope_id) == id,
                )
            )
        condition = or_(*clauses)
    return condition


def select_records(data: AuditSearch) -> Select[tuple[AuditTable]]:
    """Select and order audit records using the requested filters.

    Args:
        data: Original validated search text, filters and sort selection.

    Returns:
        Ordered SQL selection before pagination.
    """
    stmt = select(AuditTable).where(match(data.q))
    if data.actor_id is not None:
        stmt = stmt.where(col(AuditTable.actor_id).in_(data.actor_id))
    if data.action is not None:
        stmt = stmt.where(col(AuditTable.action).in_(data.action))
    if data.since is not None:
        stmt = stmt.where(col(AuditTable.created_at) >= data.since)
    if data.until is not None:
        stmt = stmt.where(col(AuditTable.created_at) < data.until)

    direction = asc if data.sort_order == SortOrder.ASC else desc
    id_order = direction(col(AuditTable.id))
    if data.sort_by == AuditSortBy.CREATED_AT:
        stmt = stmt.order_by(direction(col(AuditTable.created_at)), id_order)
    else:
        stmt = stmt.order_by(id_order)
    return stmt
