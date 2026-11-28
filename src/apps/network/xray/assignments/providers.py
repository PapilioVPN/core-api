"""Bind the Xray desired revision store and its live Panel read."""

from dishka import Provider, Scope, provide

from .app.interfaces.fleet_comparison import (
    IXrayFleetComparisonQuery,
)
from .app.interfaces.records import (
    IXrayAssignmentQuery,
    IXrayAssignmentReader,
    IXrayAssignmentRepository,
    IXrayAssignmentService,
    IXrayRevisionComparisonQuery,
)
from .app.queries.comparison import XrayRevisionComparisonQuery
from .app.queries.fleet_comparison import XrayFleetComparisonQuery
from .app.queries.records import XrayAssignmentQuery
from .app.services.records import XrayAssignmentService
from .infra.pg.readers.records import XrayAssignmentReader
from .infra.pg.repositories.records import XrayAssignmentRepository


class XrayAssignmentsProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(
        XrayAssignmentRepository, provides=IXrayAssignmentRepository
    )
    query = provide(XrayAssignmentQuery, provides=IXrayAssignmentQuery)
    service = provide(XrayAssignmentService, provides=IXrayAssignmentService)
    comparison = provide(
        XrayRevisionComparisonQuery, provides=IXrayRevisionComparisonQuery
    )
    assignment_reader = provide(
        XrayAssignmentReader, provides=IXrayAssignmentReader
    )
    fleet_comparison = provide(
        XrayFleetComparisonQuery, provides=IXrayFleetComparisonQuery
    )
