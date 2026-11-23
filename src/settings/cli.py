"""Theme and color settings for the operator CLI."""

from pydantic import BaseModel, Field


class ThemeConfig(BaseModel):
    title: str = "bold cyan"
    accent: str = "cyan"
    success: str = "bold green"
    error: str = "bold red"


class CLIConfig(BaseModel):
    color: bool = True
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
