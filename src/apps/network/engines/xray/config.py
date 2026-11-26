"""Deployment settings for Xray config validation calls."""

from pydantic import BaseModel, ConfigDict, Field


class XrayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation_timeout_seconds: float = Field(default=5, gt=0, le=30)
