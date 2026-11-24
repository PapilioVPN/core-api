"""APP-scoped host readers and system information services."""

from dishka import Provider, Scope, provide

from src.apps.core.system.info.app.interfaces import services as contracts
from src.apps.core.system.info.app.services.network import NetworkService
from src.apps.core.system.info.app.services.processes import ProcessService
from src.apps.core.system.info.app.services.resources import (
    SystemResourcesService,
)
from src.apps.core.system.info.app.services.sensors import SensorService
from src.apps.core.system.info.app.services.storage import DiskService
from src.apps.core.system.info.infra.sys.network import NetworkReader
from src.apps.core.system.info.infra.sys.processes import ProcessReader
from src.apps.core.system.info.infra.sys.resources import SystemResourcesReader
from src.apps.core.system.info.infra.sys.sensors import SensorReader
from src.apps.core.system.info.infra.sys.storage import DiskReader


class InfoInfraProvider(Provider):
    scope = Scope.APP

    resources = provide(SystemResourcesReader, scope=Scope.APP)
    disks = provide(DiskReader, scope=Scope.APP)
    network = provide(NetworkReader, scope=Scope.APP)
    processes = provide(ProcessReader, scope=Scope.APP)
    sensors = provide(SensorReader, scope=Scope.APP)


class InfoServicesProvider(Provider):
    scope = Scope.APP

    resources = provide(
        SystemResourcesService,
        provides=contracts.ISystemResourcesService,
        scope=Scope.APP,
    )
    disks = provide(
        DiskService,
        provides=contracts.IDiskService,
        scope=Scope.APP,
    )
    network = provide(
        NetworkService,
        provides=contracts.INetworkService,
        scope=Scope.APP,
    )
    processes = provide(
        ProcessService,
        provides=contracts.IProcessService,
        scope=Scope.APP,
    )
    sensors = provide(
        SensorService,
        provides=contracts.ISensorService,
        scope=Scope.APP,
    )
