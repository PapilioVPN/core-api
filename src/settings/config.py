"""Papilio settings with the Core discovery root."""

from papilio.core.config import AppConfig, HTTPConfig, Settings
from pydantic import BaseModel, ConfigDict, Field

from src.apps.core.storage.files.config import FileStorageConfig
from src.apps.shop.crypto.payments.config import CryptoPaymentsConfig
from src.settings.cli import CLIConfig

DEFAULT_HTTP = HTTPConfig(
    max_connections=8,
    max_keepalive_connections=4,
    keepalive_expiry=20,
    timeout=20,
    connect_timeout=5,
    follow_redirects=False,
)


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
        modules=["src.apps.core", "src.apps.shop"],
        tables_path="infra.pg.tables",
    )
    storage: FileStorageConfig  # pyright: ignore[reportIncompatibleVariableOverride]
    http: HTTPConfig | None = DEFAULT_HTTP
    nats: NatsConfig | None = None
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    crypto_payments: CryptoPaymentsConfig = Field(
        default_factory=CryptoPaymentsConfig
    )
