"""Expose price lookup for customer-selected custom sales."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.shop.products.volume_ranges.app.interfaces.queries import (
    IQuoteQuery,
)
from src.apps.shop.products.volume_ranges.domain.dtos.quote import QuoteInput
from src.apps.shop.products.volume_ranges.routers.schemas.quote import (
    QuoteOutput,
)

router = APIRouter(
    prefix="/public/services/{service_id:int}/volume-ranges",
    route_class=DishkaRoute,
)


@router.get("/quote")
async def get_quote(
    service_id: IdType,
    data: Annotated[QuoteInput, Query()],
    query: FromDishka[IQuoteQuery],
) -> APIResponse[QuoteOutput, None]:
    """Read the current price for a volume and optional duration.

    Args:
        service_id: Validated parent identity.
        data: Selected volume in bytes and optional duration in days.
        query: Current quote operation for storefront consumers.

    Returns:
        Validated selection and its exact integer rial price.
    """
    quote = await query.quote(service_id, data)
    return APIResponse[QuoteOutput, None].from_data(
        QuoteOutput.from_obj(quote)
    )
