"""Bind live Xray runtime metrics to native discovery."""

from dishka import Provider, Scope, provide

from .app.executions.reset import XrayResetExecution
from .app.interfaces.reset import (
    IXrayResetGateway,
    IXrayResetRepository,
    IXrayTrafficResets,
)
from .app.interfaces.runtime import IXrayRuntimeGateway, IXrayRuntimeQuery
from .app.interfaces.traffic import IXrayTrafficGateway, IXrayTrafficQuery
from .app.pipelines.reset import XrayResetPipeline
from .app.queries.runtime import XrayRuntimeQuery
from .app.queries.traffic import XrayTrafficQuery
from .app.services.reset import XrayTrafficResets
from .infra.grpc.reset import XrayResetGateway
from .infra.grpc.runtime import XrayRuntimeGateway
from .infra.grpc.traffic import XrayTrafficGateway
from .infra.pg.repositories.reset import XrayResetRepository


class XrayStatsProvider(Provider):
    scope = Scope.REQUEST

    query = provide(XrayRuntimeQuery, provides=IXrayRuntimeQuery)
    gateway = provide(
        XrayRuntimeGateway, provides=IXrayRuntimeGateway, scope=Scope.APP
    )
    traffic = provide(XrayTrafficQuery, provides=IXrayTrafficQuery)
    traffic_gateway = provide(
        XrayTrafficGateway, provides=IXrayTrafficGateway, scope=Scope.APP
    )
    resets = provide(XrayTrafficResets, provides=IXrayTrafficResets)
    reset_repo = provide(XrayResetRepository, provides=IXrayResetRepository)
    reset_gateway = provide(
        XrayResetGateway, provides=IXrayResetGateway, scope=Scope.APP
    )
    reset_execution = provide(XrayResetExecution, scope=Scope.APP)
    reset_pipeline = provide(XrayResetPipeline, scope=Scope.APP)
