"""Read issuer metadata and resolve prefixes in the administrator panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.auth.routers.dependencies.authorization import require_admin
from src.apps.shop.banking.card_prefixes.domain.types.records import (
    CardPrefixType,
)

from ...app.interfaces.queries import IBankQuery
from ...domain.dtos.records import BankList
from ..schemas.records import BankMatchOutput, BankOutput

router = APIRouter(
    prefix="/admin/banks",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("")
async def get_banks(
    query: Annotated[BankList, Query()], banks: FromDishka[IBankQuery]
) -> APIResponse[BankOutput, PagerMeta]:
    page = await banks.list(query)
    return APIResponse[BankOutput, PagerMeta](
        success=True,
        data=BankOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch")
async def get_banks_batch(
    ids: Annotated[ListIdType, Query()], banks: FromDishka[IBankQuery]
) -> APIResponse[BankOutput, None]:
    rows = await banks.get_by_ids(ids)
    return APIResponse[BankOutput, None].from_data(BankOutput.from_objs(rows))


@router.get("/prefix/{prefix}")
async def get_bank_by_prefix(
    prefix: CardPrefixType, banks: FromDishka[IBankQuery]
) -> APIResponse[BankMatchOutput, None]:
    match = await banks.get_by_prefix(prefix)
    output = BankMatchOutput(
        **match.bank.to_dict(), is_prefix_active=match.is_prefix_active
    )
    return APIResponse[BankMatchOutput, None].from_data(output)


@router.get("/{id:int}")
async def get_bank(
    id: IdType, banks: FromDishka[IBankQuery]
) -> APIResponse[BankOutput, None]:
    bank = await banks.get_by_id(id)
    return APIResponse[BankOutput, None].from_data(BankOutput.from_obj(bank))
