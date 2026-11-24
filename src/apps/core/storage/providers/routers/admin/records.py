"""Storage connection resources protected by administrator permissions."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, SlugType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.storage.providers.app.interfaces.commands import (
    IStorageProviderActivityCommand,
    IStorageProviderCreateCommand,
)
from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderService,
)
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderActivityUpdate,
    StorageProviderBatchRead,
    StorageProviderKeyBatchRead,
    StorageProviderList,
    StorageProviderUpdate,
)
from src.apps.core.storage.providers.routers.schemas.records import (
    StorageProviderCreateInput,
    StorageProviderOutput,
)

router = APIRouter(
    prefix="/admin/storage/providers",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("storage"))],
)


@router.post(
    "",
    response_model=APIResponse[StorageProviderOutput, None],
    status_code=201,
)
async def post_provider(
    data: StorageProviderCreateInput,
    command: FromDishka[IStorageProviderCreateCommand],
) -> APIResponse[StorageProviderOutput, None]:
    """Create inactive metadata and its configuration in one transaction.

    Args:
        data: Metadata and optional complete S3 configuration.
        command: Request-scoped coordinated creation contract.

    Returns:
        Stored metadata without credentials; omitted config creates {}.
    """
    provider = await command.create(data, data.config)
    output = StorageProviderOutput.from_obj(provider)
    return APIResponse[StorageProviderOutput, None].from_data(output)


@router.get("", response_model=APIResponse[StorageProviderOutput, PagerMeta])
async def get_providers(
    query: Annotated[StorageProviderList, Query()],
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, PagerMeta]:
    """Read a filtered metadata page with its total before pagination.

    Args:
        query: Native page/per_page, literal title search and activity filter.
        service: Metadata owner converting pagination to repository bounds.

    Returns:
        ID-ordered metadata and native paging information, without settings.
    """
    page = await service.list(query)
    output = StorageProviderOutput.from_objs(page.items)
    return APIResponse[StorageProviderOutput, PagerMeta](
        success=True,
        data=output,
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch", response_model=APIResponse[StorageProviderOutput, None])
async def get_provider_batch(
    query: Annotated[StorageProviderBatchRead, Query()],
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, None]:
    """Read a bounded set of connection identities.

    Args:
        query: One to 100 IDs, including possible repeats and misses.
        service: Metadata owner using the native set read.

    Returns:
        Each found connection once, omitting misses; order is unspecified.
    """
    providers = await service.get_by_ids(query)
    output = StorageProviderOutput.from_objs(providers)
    return APIResponse[StorageProviderOutput, None].from_data(output)


@router.get(
    "/keys/batch", response_model=APIResponse[StorageProviderOutput, None]
)
async def get_provider_keys_batch(
    query: Annotated[StorageProviderKeyBatchRead, Query()],
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, None]:
    """Read a bounded set of exact immutable keys.

    Args:
        query: One to 100 native slug keys in repeated query parameters.
        service: Metadata owner using one key-set selection.

    Returns:
        Found metadata once each in ID order; missing keys are omitted.
    """
    providers = await service.get_by_keys(query)
    output = StorageProviderOutput.from_objs(providers)
    return APIResponse[StorageProviderOutput, None].from_data(output)


@router.get("/key", response_model=APIResponse[StorageProviderOutput, None])
async def get_provider_key(
    key: SlugType,
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, None]:
    """Find metadata by its exact key without reserving any key spelling.

    Args:
        key: Exact stored key, supplied as a query parameter.
        service: Metadata owner; no defaults or active fallback are selected.

    Returns:
        Found metadata; native root omission leaves data absent on a miss.
    """
    provider = await service.find_by_key(key)
    output = (
        None if provider is None else StorageProviderOutput.from_obj(provider)
    )
    return APIResponse[StorageProviderOutput, None](success=True, data=output)


@router.get("/active", response_model=APIResponse[StorageProviderOutput, None])
async def get_active_provider(
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, None]:
    """Read the optional active connection's metadata.

    Args:
        service: Request-scoped metadata owner.

    Returns:
        Active metadata; data is omitted when no connection is active.
    """
    provider = await service.find_active()
    output = (
        None if provider is None else StorageProviderOutput.from_obj(provider)
    )
    return APIResponse[StorageProviderOutput, None](success=True, data=output)


@router.get("/{id}", response_model=APIResponse[StorageProviderOutput, None])
async def get_provider(
    id: IdType,
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, None]:
    """Read required connection metadata.

    Args:
        id: Native positive connection identity.
        service: Request-scoped metadata owner.

    Returns:
        Stored metadata without configuration or credentials.

    Raises:
        NotFoundException: The connection is absent.
    """
    provider = await service.get_by_id(id)
    output = StorageProviderOutput.from_obj(provider)
    return APIResponse[StorageProviderOutput, None].from_data(output)


@router.patch("/{id}", response_model=APIResponse[StorageProviderOutput, None])
async def patch_provider(
    id: IdType,
    data: StorageProviderUpdate,
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, None]:
    """Patch descriptions while retaining immutable key and activity.

    Args:
        id: Native positive connection identity.
        data: Explicit title/description changes; null clears description.
        service: Metadata owner checking the recognized patch and committing.

    Returns:
        Updated metadata, preserving omitted fields and nested nulls.
    """
    provider = await service.update(id, data)
    output = StorageProviderOutput.from_obj(provider)
    return APIResponse[StorageProviderOutput, None].from_data(output)


@router.delete(
    "/{id}", response_model=APIResponse[StorageProviderOutput, None]
)
async def delete_provider(
    id: IdType,
    service: FromDishka[IStorageProviderService],
) -> APIResponse[StorageProviderOutput, None]:
    """Delete a connection and cascade its configuration.

    Args:
        id: Native positive connection identity.
        service: Metadata owner committing the deletion.

    Returns:
        Previous metadata without credentials.
    """
    provider = await service.remove(id)
    output = StorageProviderOutput.from_obj(provider)
    return APIResponse[StorageProviderOutput, None].from_data(output)


@router.patch(
    "/{id}/activity", response_model=APIResponse[StorageProviderOutput, None]
)
async def patch_provider_activity(
    id: IdType,
    data: StorageProviderActivityUpdate,
    command: FromDishka[IStorageProviderActivityCommand],
) -> APIResponse[StorageProviderOutput, None]:
    """Change activity through the atomic single-active switching command.

    Args:
        id: Native positive target connection identity.
        data: True switches to this connection; False disables only it.
        command: Owning request-scoped activation coordinator.

    Returns:
        Updated target metadata; an empty configuration may be activated.
    """
    provider = await command.update(id, data)
    output = StorageProviderOutput.from_obj(provider)
    return APIResponse[StorageProviderOutput, None].from_data(output)
