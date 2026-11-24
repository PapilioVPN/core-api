"""Papilio settings with the Core discovery root."""

from papilio.core.config import AppConfig, Settings
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PositiveFloat

from src.apps.core.storage.files.config import FileStorageConfig
from src.settings.cli import CLIConfig


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


class OCRConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    url: HttpUrl
    timeout: PositiveFloat = 20
    min_score: float = Field(default=0.85, ge=0, le=1)


class CoreSettings(Settings):
    app: AppConfig = AppConfig(
        modules=["src.apps.core", "src.apps.shop"],
        tables_path="infra.pg.tables",
    )
    storage: FileStorageConfig  # pyright: ignore[reportIncompatibleVariableOverride]
    nats: NatsConfig | None = None
    ocr: OCRConfig | None = None
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
