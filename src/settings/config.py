"""Papilio settings with the Core discovery root."""

from papilio.core.config import AppConfig, Settings
from pydantic import BaseModel, Field

from src.settings.cli import CLIConfig


class NatsConfig(BaseModel):
    servers: list[str] = Field(min_length=1, repr=False)
    connect_timeout: int = Field(default=5, gt=0)
    graceful_timeout: float = Field(default=15, gt=0)


class SchedulerConfig(BaseModel):
    stream: str = "papiliovpn_core_jobs"
    subject: str = "papiliovpn.core.jobs"
    durable: str = "papiliovpn_core_workers"


class CoreSettings(Settings):
    app: AppConfig = AppConfig(
        modules=["src.apps.core"], tables_path="infra.pg.tables"
    )
    nats: NatsConfig | None = None
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
