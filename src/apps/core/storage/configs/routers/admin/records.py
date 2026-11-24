"""Read and replace the application's single storage destination setting."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.storage.configs.app.interfaces.services import (
    IStorageConfigService,
)
from src.apps.core.storage.configs.domain.dtos.storage import (
    StorageConfigWrite,
)
from src.apps.core.storage.configs.routers.schemas.storage import (
    StorageConfigOutput,
)

router = APIRouter(
    prefix="/admin/storage/config",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("storage"))],
)


@router.get("", response_model=APIResponse[StorageConfigOutput, None])
async def get_config(
    service: FromDishka[IStorageConfigService],
) -> APIResponse[StorageConfigOutput, None]:
    """Read the saved global destination selection.

    Args:
        service: Request-scoped storage setting owner.

    Returns:
        The stored backend and native record metadata.

    Raises:
        NotFoundException: No global selection has been saved.
    """
    configuration = await service.get_current()
    output = StorageConfigOutput.from_obj(configuration)
    return APIResponse[StorageConfigOutput, None].from_data(output)


@router.put("", response_model=APIResponse[StorageConfigOutput, None])
async def put_config(
    data: StorageConfigWrite,
    service: FromDishka[IStorageConfigService],
) -> APIResponse[StorageConfigOutput, None]:
    """Create or replace the single global backend selection.

    Args:
        data: Explicit local or S3 backend selection.
        service: Request-scoped owner of the committing save.

    Returns:
        The saved setting, preserving its identity and creation time.
    """
    configuration = await service.save(data)
    output = StorageConfigOutput.from_obj(configuration)
    return APIResponse[StorageConfigOutput, None].from_data(output)
