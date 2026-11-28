"""Bind Xray lifecycle operations and status reads."""

from dishka import Provider, Scope, provide

from .app.commands.apply import XrayApplyCommand
from .app.commands.fleet_apply import XrayFleetApplyCommand
from .app.commands.fleet_start import XrayFleetStartCommand
from .app.commands.fleet_stop import XrayFleetStopCommand
from .app.commands.restart import XrayRestartCommand
from .app.commands.rollout import RestartRolloutCommand
from .app.executions.rollout import RestartRolloutExecution
from .app.executions.start import XrayStartExecution
from .app.interfaces.apply import IXrayApplyCommand
from .app.interfaces.fleet import (
    IXrayFleetStartCommand,
    IXrayFleetStartQuery,
    IXrayFleetStopCommand,
    IXrayFleetStopQuery,
)
from .app.interfaces.fleet_apply import (
    IXrayFleetApplyCommand,
    IXrayFleetApplyQuery,
)
from .app.interfaces.restart import IXrayRestartCommand
from .app.interfaces.rollout import (
    IRestartRolloutAdmission,
    IRestartRolloutProgress,
    IRestartRolloutQuery,
    IRestartRolloutReader,
    IRestartRolloutRepository,
)
from .app.interfaces.start import (
    IXrayStartAdmission,
    IXrayStartGateway,
    IXrayStartQuery,
    IXrayStartRepository,
)
from .app.interfaces.status import (
    IXrayFleetStatusQuery,
    IXrayStatusFanout,
    IXrayStatusGateway,
    IXrayStatusQuery,
)
from .app.pipelines.control import XrayControlPipeline
from .app.pipelines.rollout import RestartRolloutPipeline
from .app.pipelines.start import XrayStartPipeline
from .app.queries.fleet import (
    XrayFleetApplyQuery,
    XrayFleetStartQuery,
    XrayFleetStopQuery,
)
from .app.queries.fleet_status import XrayFleetStatusQuery
from .app.queries.rollout import RestartRolloutQuery
from .app.queries.start import XrayStartQuery
from .app.queries.status import XrayStatusQuery
from .app.services.admission import XrayStartAdmission
from .app.services.fleet_admission import XrayFleetAdmission
from .app.services.rollout_progress import RestartRolloutProgress
from .app.services.rollout_schedule import RestartRolloutSchedule
from .app.services.status_fanout import XrayStatusFanout
from .infra.grpc.start import XrayStartGateway
from .infra.grpc.status import XrayStatusGateway
from .infra.pg.readers.rollout import RestartRolloutReader
from .infra.pg.repositories.rollout import RestartRolloutRepository
from .infra.pg.repositories.start import XrayStartRepository


class XrayInstancesProvider(Provider):
    scope = Scope.REQUEST

    status_gateway = provide(
        XrayStatusGateway, provides=IXrayStatusGateway, scope=Scope.APP
    )
    status = provide(XrayStatusQuery, provides=IXrayStatusQuery)
    status_fanout = provide(
        XrayStatusFanout, provides=IXrayStatusFanout, scope=Scope.APP
    )
    fleet_status = provide(
        XrayFleetStatusQuery, provides=IXrayFleetStatusQuery
    )
    apply_command = provide(XrayApplyCommand, provides=IXrayApplyCommand)
    fleet_admission = provide(XrayFleetAdmission)
    fleet_apply = provide(
        XrayFleetApplyCommand, provides=IXrayFleetApplyCommand
    )
    fleet_apply_query = provide(
        XrayFleetApplyQuery, provides=IXrayFleetApplyQuery
    )
    fleet_start = provide(
        XrayFleetStartCommand, provides=IXrayFleetStartCommand
    )
    fleet_start_query = provide(
        XrayFleetStartQuery, provides=IXrayFleetStartQuery
    )
    fleet_stop = provide(XrayFleetStopCommand, provides=IXrayFleetStopCommand)
    fleet_stop_query = provide(
        XrayFleetStopQuery, provides=IXrayFleetStopQuery
    )
    restart_command = provide(XrayRestartCommand, provides=IXrayRestartCommand)
    start_admission = provide(XrayStartAdmission, provides=IXrayStartAdmission)
    start_query = provide(XrayStartQuery, provides=IXrayStartQuery)
    start_repo = provide(XrayStartRepository, provides=IXrayStartRepository)
    start_gateway = provide(
        XrayStartGateway, provides=IXrayStartGateway, scope=Scope.APP
    )
    start_execution = provide(XrayStartExecution, scope=Scope.APP)
    start_pipeline = provide(XrayStartPipeline, scope=Scope.APP)
    control_pipeline = provide(XrayControlPipeline, scope=Scope.APP)
    rollout_repo = provide(
        RestartRolloutRepository, provides=IRestartRolloutRepository
    )
    rollout_reader = provide(
        RestartRolloutReader, provides=IRestartRolloutReader
    )
    rollout_query = provide(RestartRolloutQuery, provides=IRestartRolloutQuery)
    rollout_schedule = provide(RestartRolloutSchedule)
    rollout_progress = provide(
        RestartRolloutProgress, provides=IRestartRolloutProgress
    )
    rollout_admission = provide(
        RestartRolloutCommand, provides=IRestartRolloutAdmission
    )
    rollout_execution = provide(RestartRolloutExecution, scope=Scope.APP)
    rollout_pipeline = provide(RestartRolloutPipeline, scope=Scope.APP)
