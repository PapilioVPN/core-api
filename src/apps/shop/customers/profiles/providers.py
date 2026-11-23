"""Bind customer record operations and search to the request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.queries import IProfileSearch
from .app.interfaces.services import IProfileCRUD
from .app.queries.search import ProfileSearchQuery
from .app.services.crud import ProfileCRUD
from .infra.pg.readers.search import ProfileReader
from .infra.pg.repositories.crud import ProfileRepository


class ProfileProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ProfileRepository)
    crud = provide(ProfileCRUD, provides=IProfileCRUD)
    reader = provide(ProfileReader)
    search = provide(ProfileSearchQuery, provides=IProfileSearch)
