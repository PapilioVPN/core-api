"""Theme and color settings for the operator CLI."""

from pydantic import BaseModel, ConfigDict, Field


class ThemeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = "bold cyan"
    accent: str = "cyan"
    success: str = "bold green"
    error: str = "bold red"


class CLIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    color: bool = True
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
