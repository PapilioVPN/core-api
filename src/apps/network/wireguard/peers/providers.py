"""Bind WireGuard peer membership to Panel discovery."""

from dishka import Provider, Scope, provide

from .app.interfaces.membership import (
    IWireGuardMembershipGateway,
    IWireGuardMembershipQuery,
)
from .app.queries.membership import WireGuardMembershipQuery
from .infra.grpc.membership import WireGuardMembershipGateway


class WireGuardPeersProvider(Provider):
    scope = Scope.REQUEST

    membership = provide(
        WireGuardMembershipQuery, provides=IWireGuardMembershipQuery
    )
    gateway = provide(
        WireGuardMembershipGateway,
        provides=IWireGuardMembershipGateway,
        scope=Scope.APP,
    )
