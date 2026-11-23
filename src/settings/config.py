"""Papilio settings with the Core discovery root."""

from papilio.core.config import AppConfig, Settings
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.settings.cli import CLIConfig

MODULES = ("src.apps.core", "src.apps.catalog")


class NatsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    servers: list[str] = Field(min_length=1, repr=False)
    connect_timeout: int = Field(default=5, gt=0)
    graceful_timeout: float = Field(default=15, gt=0)


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream: str = Field(default="papiliovpn_core_jobs", min_length=1)
    subject: str = Field(default="papiliovpn.core.jobs", min_length=1)
    durable: str = Field(default="papiliovpn_core_workers", min_length=1)


class CoreSettings(Settings):
    app: AppConfig = AppConfig(
        modules=list(MODULES), tables_path="infra.pg.tables"
    )
    nats: NatsConfig | None = None
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)

    @field_validator("app")
    @classmethod
    def include_catalog(cls, app: AppConfig) -> AppConfig:
        """Upgrade discovery for configs generated before the catalog."""
        if app.modules == ["src.apps.core"]:
            app = app.model_copy(update={"modules": list(MODULES)})
        return app
