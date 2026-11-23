"""Compose module commands and their native application scope."""

import typer
from dishka import make_async_container
from papilio.core.bootstrap import Bootstrapper
from papilio.core.config import get_settings
from papilio.providers.base import CoreProvider
from rich.console import Console
from rich.theme import Theme

from src.apps.core.users.cli.owner import cli as users
from src.bootstrap.providers.infra import infra_providers
from src.settings.config import CoreSettings
from src.shared.cli import CLI

app = typer.Typer(
    help="[bold cyan]PapilioVPN[/] Core operator commands.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)
app.add_typer(users, name="users")


def load() -> CLI:
    """Construct the command's container and console from native settings."""
    settings = get_settings(CoreSettings)
    theme = Theme(settings.cli.theme.model_dump())
    console = Console(theme=theme, no_color=not settings.cli.color)
    discover = Bootstrapper(
        settings.app.modules, tables_path=settings.app.tables_path
    )
    container = make_async_container(
        CoreProvider(settings),
        *infra_providers(settings),
        *discover.boot_providers(),
    )
    return CLI(container, console)


@app.callback()
def setup(ctx: typer.Context) -> None:
    """Provide command resources on demand during actual execution."""
    ctx.obj = load
