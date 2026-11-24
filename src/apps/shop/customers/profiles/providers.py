"""Bind customer record operations and search to the request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.queries import IProfileSearch
from .app.interfaces.services import ICustomerService
from .app.queries.search import ProfileSearchQuery
from .app.services.crud import CustomerService
from .infra.pg.readers.search import ProfileReader
from .infra.pg.repositories.crud import CustomerRepository


class ProfileProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CustomerRepository)
    service = provide(CustomerService, provides=ICustomerService)
    reader = provide(ProfileReader)
    search = provide(ProfileSearchQuery, provides=IProfileSearch)
