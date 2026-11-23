"""Search and filter administrator audit history."""

from datetime import timedelta
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta, SortMeta

from src.apps.core.audit.app.queries.search import AuditQuery
from src.apps.core.audit.domain.dtos.search import AuditSearch
from src.apps.core.audit.domain.enums.sorts import AuditSortBy
from src.apps.core.audit.domain.results.filters import AuditOptions
from src.apps.core.audit.routers.schemas.records import AuditOutput
from src.apps.core.audit.routers.schemas.search import (
    AuditMeta,
    FilterOutput,
    OptionOutput,
    TermOutput,
    TimeOutput,
)
from src.apps.core.auth.routers.dependencies.authorization import (
    require_admin,
)

router = APIRouter(
    prefix="/admin/audit",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("audit"))],
)


def _filters(options: AuditOptions) -> list[FilterOutput]:
    """Render the variant-search filter array with UTC Unix-second bounds."""
    upper = options.last + timedelta(microseconds=1) if options.last else None
    return [
        TermOutput(
            key="actor_id",
            title="ادمین",
            options=[
                OptionOutput(id=id, label=f"#{id}", count=count)
                for id, count in options.actors.items()
            ],
        ),
        TermOutput(
            key="action",
            title="عملیات",
            options=[
                OptionOutput(id=action, label=action.fa, count=count)
                for action, count in options.actions.items()
            ],
        ),
        TimeOutput(
            minimum=options.first.timestamp() if options.first else None,
            maximum=upper.timestamp() if upper else None,
        ),
    ]


@router.get("", response_model=APIResponse[AuditOutput, AuditMeta])
async def get_audit(
    data: Annotated[AuditSearch, Query()],
    query: FromDishka[AuditQuery],
) -> APIResponse[AuditOutput, AuditMeta]:
    """Search operations and return facets over all text matches."""
    page = await query.search(data)
    options = await query.get_options(data)
    output = AuditOutput.from_objs(page.items)
    return APIResponse[AuditOutput, AuditMeta](
        success=True,
        data=output,
        meta=AuditMeta(
            pager=PagerMeta.from_total(
                data.page, data.per_page, page.total_items
            ),
            filters=_filters(options),
            sorts=SortMeta.of(AuditSortBy),
        ),
    )
