"""Card prefix resources protected by banking operation permissions."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.records import ICardPrefixCommand, ICardPrefixCRUD
from ...domain.dtos.records import (
    CardPrefixCreate,
    CardPrefixList,
    CardPrefixUpdate,
)
from ...domain.types.records import CardPrefixType
from ..schemas.records import CardPrefixOutput

router = APIRouter(
    prefix="/admin/card-prefixes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post(
    "", response_model=APIResponse[CardPrefixOutput, None], status_code=201
)
async def post_card_prefix(
    data: CardPrefixCreate,
    command: FromDishka[ICardPrefixCommand],
) -> APIResponse[CardPrefixOutput, None]:
    """Create a unique card prefix under an existing bank.

    Args:
        data: Validated prefix text, bank and activity fields.
        command: Prefix write owner checking the bank reference.

    Returns:
        The stored prefix in the native response envelope.
    """
    record = await command.create(data)
    output = CardPrefixOutput.from_obj(record)
    return APIResponse[CardPrefixOutput, None].from_data(output)


@router.get("", response_model=APIResponse[CardPrefixOutput, PagerMeta])
async def get_card_prefixes(
    query: Annotated[CardPrefixList, Query()],
    service: FromDishka[ICardPrefixCRUD],
) -> APIResponse[CardPrefixOutput, PagerMeta]:
    """Read an ID-ordered page filtered by bank and activity.

    Args:
        query: Validated pagination and optional reference filters.
        service: Prefix owner converting pagination to retrieval bounds.

    Returns:
        Prefix outputs and native metadata for the filtered total.
    """
    page = await service.list(query)
    output = CardPrefixOutput.from_objs(page.items)
    return APIResponse[CardPrefixOutput, PagerMeta](
        success=True,
        data=output,
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch", response_model=APIResponse[CardPrefixOutput, None])
async def get_card_prefix_batch(
    ids: Annotated[ListIdType, Query()],
    service: FromDishka[ICardPrefixCRUD],
) -> APIResponse[CardPrefixOutput, None]:
    """Read a bounded set of prefix records by identity.

    Args:
        ids: One to 100 positive identities in repeated query parameters.
        service: Request-scoped prefix service.

    Returns:
        Unique matches including inactive records, omitting missing IDs;
        result order is unspecified.
    """
    records = await service.get_by_ids(ids)
    output = CardPrefixOutput.from_objs(records)
    return APIResponse[CardPrefixOutput, None].from_data(output)


@router.get(
    "/prefixes/batch", response_model=APIResponse[CardPrefixOutput, None]
)
async def get_card_prefix_text_batch(
    prefixes: Annotated[
        list[CardPrefixType], Query(min_length=1, max_length=100)
    ],
    service: FromDishka[ICardPrefixCRUD],
) -> APIResponse[CardPrefixOutput, None]:
    """Read a bounded set of exact prefix texts.

    Args:
        prefixes: One to 100 prefix strings in repeated query parameters.
        service: Request-scoped prefix service.

    Returns:
        Unique matches including inactive records, omitting missing prefixes;
        result order is unspecified.
    """
    records = await service.get_by_prefixes(prefixes)
    output = CardPrefixOutput.from_objs(records)
    return APIResponse[CardPrefixOutput, None].from_data(output)


@router.get("/prefix", response_model=APIResponse[CardPrefixOutput, None])
async def get_card_prefix_by_text(
    prefix: CardPrefixType,
    service: FromDishka[ICardPrefixCRUD],
) -> APIResponse[CardPrefixOutput, None]:
    """Read a required prefix record by its exact text.

    Args:
        prefix: Validated numeric text, preserving leading zeros.
        service: Request-scoped prefix service.

    Returns:
        The stored prefix record, including inactive records.

    Raises:
        NotFoundException: The prefix is absent.
    """
    record = await service.get_by_prefix(prefix)
    output = CardPrefixOutput.from_obj(record)
    return APIResponse[CardPrefixOutput, None].from_data(output)


@router.get("/{id:int}", response_model=APIResponse[CardPrefixOutput, None])
async def get_card_prefix(
    id: IdType,
    service: FromDishka[ICardPrefixCRUD],
) -> APIResponse[CardPrefixOutput, None]:
    """Read a required prefix record by identity.

    Args:
        id: Validated prefix record identity.
        service: Request-scoped prefix service.

    Returns:
        The stored record; absence gives the native 404.
    """
    record = await service.get_by_id(id)
    output = CardPrefixOutput.from_obj(record)
    return APIResponse[CardPrefixOutput, None].from_data(output)


@router.patch("/{id:int}", response_model=APIResponse[CardPrefixOutput, None])
async def patch_card_prefix(
    id: IdType,
    data: CardPrefixUpdate,
    command: FromDishka[ICardPrefixCommand],
) -> APIResponse[CardPrefixOutput, None]:
    """Update supplied prefix fields after checking any new bank.

    Args:
        id: Validated prefix record identity.
        data: Validated patch preserving omitted fields.
        command: Prefix write owner checking the bank reference.

    Returns:
        The updated prefix record in the native envelope.
    """
    record = await command.update(id, data)
    output = CardPrefixOutput.from_obj(record)
    return APIResponse[CardPrefixOutput, None].from_data(output)


@router.delete("/{id:int}", response_model=APIResponse[CardPrefixOutput, None])
async def delete_card_prefix(
    id: IdType,
    service: FromDishka[ICardPrefixCRUD],
) -> APIResponse[CardPrefixOutput, None]:
    """Remove a prefix record through its owning service.

    Args:
        id: Validated prefix record identity.
        service: Request-scoped prefix write owner.

    Returns:
        The removed record; absence gives the native 404.
    """
    record = await service.remove(id)
    output = CardPrefixOutput.from_obj(record)
    return APIResponse[CardPrefixOutput, None].from_data(output)
