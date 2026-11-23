"""APP-scoped health probes and focused services."""

from dishka import Provider, Scope, provide

from src.apps.core.system.app.interfaces import health as contracts
from src.apps.core.system.app.services.info import PublicHealthService
from src.apps.core.system.app.services.network import (
    NetworkHealthService,
)
from src.apps.core.system.app.services.pg import PostgresHealthService
from src.apps.core.system.app.services.processes import (
    ProcessHealthService,
)
from src.apps.core.system.app.services.redis import RedisHealthService
from src.apps.core.system.app.services.resources import (
    SystemResourcesService,
)
from src.apps.core.system.app.services.sensors import (
    SensorHealthService,
)
from src.apps.core.system.app.services.storage import DiskHealthService
from src.apps.core.system.infra.ping.pg import PostgresPing
from src.apps.core.system.infra.ping.redis import RedisPing
from src.apps.core.system.infra.sys.network import NetworkReader
from src.apps.core.system.infra.sys.processes import ProcessReader
from src.apps.core.system.infra.sys.resources import (
    SystemResourcesReader,
)
from src.apps.core.system.infra.sys.sensors import SensorReader
from src.apps.core.system.infra.sys.storage import DiskReader


class HealthInfraProvider(Provider):
    scope = Scope.APP

    postgres = provide(PostgresPing, scope=Scope.APP)
    redis = provide(RedisPing, scope=Scope.APP)
    resources = provide(SystemResourcesReader, scope=Scope.APP)
    disks = provide(DiskReader, scope=Scope.APP)
    network = provide(NetworkReader, scope=Scope.APP)
    processes = provide(ProcessReader, scope=Scope.APP)
    sensors = provide(SensorReader, scope=Scope.APP)


class HealthServicesProvider(Provider):
    scope = Scope.APP

    public = provide(
        PublicHealthService,
        provides=contracts.IPublicHealthService,
        scope=Scope.APP,
    )
    postgres = provide(
        PostgresHealthService,
        provides=contracts.IPostgresHealthService,
        scope=Scope.APP,
    )
    redis = provide(
        RedisHealthService,
        provides=contracts.IRedisHealthService,
        scope=Scope.APP,
    )
    resources = provide(
        SystemResourcesService,
        provides=contracts.ISystemResourcesService,
        scope=Scope.APP,
    )
    disks = provide(
        DiskHealthService,
        provides=contracts.IDiskHealthService,
        scope=Scope.APP,
    )
    network = provide(
        NetworkHealthService,
        provides=contracts.INetworkHealthService,
        scope=Scope.APP,
    )
    processes = provide(
        ProcessHealthService,
        provides=contracts.IProcessHealthService,
        scope=Scope.APP,
    )
    sensors = provide(
        SensorHealthService,
        provides=contracts.ISensorHealthService,
        scope=Scope.APP,
    )
