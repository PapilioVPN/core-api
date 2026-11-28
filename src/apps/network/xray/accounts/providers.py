"""Bind the aggregate account observation through native discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.count import IXrayVlessCountGateway, IXrayVlessCountQuery
from .app.queries.count import XrayVlessCountQuery
from .infra.grpc.count import XrayVlessCountGateway


class XrayAccountsProvider(Provider):
    scope = Scope.REQUEST

    query = provide(XrayVlessCountQuery, provides=IXrayVlessCountQuery)
    gateway = provide(
        XrayVlessCountGateway, provides=IXrayVlessCountGateway, scope=Scope.APP
    )
