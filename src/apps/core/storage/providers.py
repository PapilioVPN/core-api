"""Bind local file storage to the application's native settings."""

from dishka import Provider, Scope, provide

from .app.interfaces.files import IFileStorage
from .infra.local import LocalStorage


class StorageProvider(Provider):
    scope = Scope.APP

    files = provide(LocalStorage, provides=IFileStorage)
