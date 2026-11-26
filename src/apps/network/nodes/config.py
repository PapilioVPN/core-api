"""Private deployment configuration for authenticated Node host reads."""

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    SecretStr,
    field_validator,
)

from .domain.dtos.records import NodeAddress, NodePort


class NodeHostTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    address: NodeAddress
    port: NodePort
    api_key: SecretStr = Field(min_length=1, repr=False)
    ca_pem: str | None = Field(default=None, min_length=1)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: SecretStr) -> SecretStr:
        """Reject keys that cannot be sent as gRPC ASCII metadata."""
        if any(
            not 33 <= ord(char) <= 126 for char in value.get_secret_value()
        ):
            raise ValueError("API key must contain visible ASCII characters")
        return value


class NodeCheckConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interval_seconds: int | None = Field(default=60, gt=0, strict=True)
    stale_after_seconds: int = Field(default=180, gt=0, strict=True)
    batch_size: int = Field(default=32, ge=1, le=100, strict=True)
    concurrency: int = Field(default=8, ge=1, le=16, strict=True)


class NodeHostConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    timeout_seconds: float = Field(default=3, gt=0, le=30)
    targets: dict[PositiveInt, NodeHostTarget] = Field(default_factory=dict)
    checks: NodeCheckConfig = Field(default_factory=NodeCheckConfig)
