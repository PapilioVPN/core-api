"""Expose public catalog offer details."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.shop.catalogs.app.interfaces.public import IPublicCatalogQuery
from src.apps.shop.catalogs.routers.schemas.public import PublicCatalogOutput

router = APIRouter(prefix="/public/catalogs", route_class=DishkaRoute)


@router.get("/{id:int}")
async def get_catalog(
    id: IdType, query: FromDishka[IPublicCatalogQuery]
) -> APIResponse[PublicCatalogOutput, None]:
    """Read one visible offer by catalog ID.

    Args:
        id: Validated public catalog identity.
        query: Public offer detail query.

    Returns:
        The offer's public fields in the native envelope.

    Raises:
        NotFoundException: The offer is absent or hidden.
    """
    offer = await query.get_by_id(id)
    output = PublicCatalogOutput.from_obj(offer)
    return APIResponse[PublicCatalogOutput, None].from_data(output)
