"""Configure receiving cards in the administrator panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.auth.routers.dependencies.authorization import require_admin

from ...app.interfaces.commands import ICardCommand
from ...app.interfaces.services import ICardCRUD
from ...domain.dtos.records import CardCreate, CardList, CardUpdate
from ..schemas.records import CardOutput

router = APIRouter(
    prefix="/admin/payment-cards",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_card(
    data: CardCreate, command: FromDishka[ICardCommand]
) -> APIResponse[CardOutput, None]:
    card = await command.create(data)
    return APIResponse[CardOutput, None].from_data(CardOutput.from_obj(card))


@router.get("")
async def get_cards(
    query: Annotated[CardList, Query()], cards: FromDishka[ICardCRUD]
) -> APIResponse[CardOutput, PagerMeta]:
    page = await cards.list(query)
    return APIResponse[CardOutput, PagerMeta](
        success=True,
        data=CardOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch")
async def get_cards_batch(
    ids: Annotated[ListIdType, Query()], cards: FromDishka[ICardCRUD]
) -> APIResponse[CardOutput, None]:
    rows = await cards.get_by_ids(ids)
    return APIResponse[CardOutput, None].from_data(CardOutput.from_objs(rows))


@router.get("/{id:int}")
async def get_card(
    id: IdType, cards: FromDishka[ICardCRUD]
) -> APIResponse[CardOutput, None]:
    card = await cards.get_by_id(id)
    return APIResponse[CardOutput, None].from_data(CardOutput.from_obj(card))


@router.patch("/{id:int}")
async def patch_card(
    id: IdType, data: CardUpdate, command: FromDishka[ICardCommand]
) -> APIResponse[CardOutput, None]:
    card = await command.update(id, data)
    return APIResponse[CardOutput, None].from_data(CardOutput.from_obj(card))


@router.delete("/{id:int}")
async def delete_card(
    id: IdType, cards: FromDishka[ICardCRUD]
) -> APIResponse[CardOutput, None]:
    card = await cards.remove(id)
    return APIResponse[CardOutput, None].from_data(CardOutput.from_obj(card))
