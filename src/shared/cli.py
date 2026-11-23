"""Resources borrowed by module-owned CLI commands."""

from dataclasses import dataclass

from dishka import AsyncContainer
from rich.console import Console


@dataclass(frozen=True, slots=True)
class CLI:
    container: AsyncContainer
    console: Console
