"""Bind volume operations to Papilio's request scope."""

from dishka import Provider, Scope, provide

from src.apps.shop.volumes.app.services.records import Volumes
from src.apps.shop.volumes.infra.pg.repositories.records import (
    VolumeRepository,
)


class VolumesProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(VolumeRepository)
    volumes = provide(Volumes)
