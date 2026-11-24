"""Bind volume operations to Papilio's request scope."""

from dishka import Provider, Scope, provide

from src.apps.shop.products.volumes.app.interfaces.services import (
    IVolumeService,
)
from src.apps.shop.products.volumes.app.services.crud import VolumeService
from src.apps.shop.products.volumes.infra.pg.repositories.crud import (
    VolumeRepository,
)


class VolumesProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(VolumeRepository)
    volumes = provide(VolumeService, provides=IVolumeService)
