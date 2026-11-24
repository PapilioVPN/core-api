"""One-to-one S3 configuration resources with safe public output."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.storage.providers.app.interfaces.commands import (
    IStorageProviderConfigCommand,
)
from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderConfigService,
)
from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderBatchRead,
)
from src.apps.core.storage.providers.routers.mappers.records import (
    StorageProviderConfigMapper,
)
from src.apps.core.storage.providers.routers.schemas.configs import (
    StorageProviderConfigOutput,
)

router = APIRouter(
    prefix="/admin/storage/providers",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("storage"))],
)


@router.get(
    "/configs/batch",
    response_model=APIResponse[StorageProviderConfigOutput, None],
)
async def get_config_batch(
    query: Annotated[StorageProviderBatchRead, Query()],
    service: FromDishka[IStorageProviderConfigService],
) -> APIResponse[StorageProviderConfigOutput, None]:
    """Read a bounded set of configurations through one native set query.

    Args:
        query: One to 100 parent IDs, allowing misses and repeated IDs.
        service: Request-scoped configuration record owner.

    Returns:
        Found configurations once each, with credential-presence flags only.
        Missing parents/configurations omit; ordering is unspecified.
    """
    configurations = await service.get_by_provider_ids(query)
    output = [
        StorageProviderConfigMapper.to_output(row) for row in configurations
    ]
    return APIResponse[StorageProviderConfigOutput, None].from_data(output)


@router.get(
    "/{id}/config",
    response_model=APIResponse[StorageProviderConfigOutput, None],
)
async def get_config(
    id: IdType,
    service: FromDishka[IStorageProviderConfigService],
) -> APIResponse[StorageProviderConfigOutput, None]:
    """Read public settings for the recorded connection, active or inactive.

    Args:
        id: Native positive parent identity.
        service: Configuration owner; no usable-connection check is needed.

    Returns:
        Stored non-sensitive settings and credential-presence flags. Empty
        configuration preserves null fields rather than inventing defaults.

    Raises:
        NotFoundException: The configuration record is absent.
    """
    configuration = await service.get_by_provider_id(id)
    output = StorageProviderConfigMapper.to_output(configuration)
    return APIResponse[StorageProviderConfigOutput, None].from_data(output)


@router.put(
    "/{id}/config",
    response_model=APIResponse[StorageProviderConfigOutput, None],
)
async def put_config(
    id: IdType,
    data: S3Config,
    command: FromDishka[IStorageProviderConfigCommand],
) -> APIResponse[StorageProviderConfigOutput, None]:
    """Replace the full S3 configuration after the command checks its parent.

    Args:
        id: Native positive parent connection identity.
        data: Complete validated replacement settings including credentials.
        command: Request-scoped configuration coordination owner.

    Returns:
        Public replacement settings and credential-presence flags only.

    Raises:
        NotFoundException: The parent or its configuration is absent.
    """
    configuration = await command.update(id, data)
    output = StorageProviderConfigMapper.to_output(configuration)
    return APIResponse[StorageProviderConfigOutput, None].from_data(output)
