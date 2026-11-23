"""Bind range CRUD, configuration, and public queries."""

from dishka import Provider, Scope, provide

from src.apps.shop.volume_ranges.app.commands.records import RangeCommand
from src.apps.shop.volume_ranges.app.interfaces.commands import IRangeCommand
from src.apps.shop.volume_ranges.app.interfaces.queries import (
    IPublicRangeQuery,
    IQuoteQuery,
)
from src.apps.shop.volume_ranges.app.interfaces.services import IRangeCRUD
from src.apps.shop.volume_ranges.app.queries.public import PublicRangeQuery
from src.apps.shop.volume_ranges.app.queries.quote import QuoteQuery
from src.apps.shop.volume_ranges.app.services.crud import RangeCRUD
from src.apps.shop.volume_ranges.infra.pg.readers.public import (
    PublicRangeReader,
)
from src.apps.shop.volume_ranges.infra.pg.readers.quote import QuoteReader
from src.apps.shop.volume_ranges.infra.pg.repositories.crud import (
    RangeRepository,
)


class RangeProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(RangeRepository)
    crud = provide(RangeCRUD, provides=IRangeCRUD)
    command = provide(RangeCommand, provides=IRangeCommand)
    public_reader = provide(PublicRangeReader)
    public = provide(PublicRangeQuery, provides=IPublicRangeQuery)
    quote_reader = provide(QuoteReader)
    quote = provide(QuoteQuery, provides=IQuoteQuery)
