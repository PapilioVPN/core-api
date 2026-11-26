"""Bind range CRUD, configuration, and public queries."""

from dishka import Provider, Scope, provide

from src.apps.shop.products.volume_ranges.app.commands.records import (
    RangeCreateCommand,
    RangeReplaceCommand,
)
from src.apps.shop.products.volume_ranges.app.interfaces.commands import (
    IRangeCreateCommand,
    IRangeReplaceCommand,
)
from src.apps.shop.products.volume_ranges.app.interfaces.queries import (
    IPublicRangeQuery,
    IQuoteQuery,
)
from src.apps.shop.products.volume_ranges.app.interfaces.services import (
    IVolumeRangeService,
)
from src.apps.shop.products.volume_ranges.app.queries.public import (
    PublicRangeQuery,
)
from src.apps.shop.products.volume_ranges.app.queries.quote import QuoteQuery
from src.apps.shop.products.volume_ranges.app.services.crud import (
    VolumeRangeService,
)
from src.apps.shop.products.volume_ranges.infra.pg.readers.public import (
    PublicRangeReader,
)
from src.apps.shop.products.volume_ranges.infra.pg.readers.quote import (
    QuoteReader,
)
from src.apps.shop.products.volume_ranges.infra.pg.repositories.crud import (
    VolumeRangeRepository,
)


class RangeProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(VolumeRangeRepository)
    service = provide(VolumeRangeService, provides=IVolumeRangeService)
    create_command = provide(RangeCreateCommand, provides=IRangeCreateCommand)
    replace_command = provide(
        RangeReplaceCommand, provides=IRangeReplaceCommand
    )
    public_reader = provide(PublicRangeReader)
    public = provide(PublicRangeQuery, provides=IPublicRangeQuery)
    quote_reader = provide(QuoteReader)
    quote = provide(QuoteQuery, provides=IQuoteQuery)
