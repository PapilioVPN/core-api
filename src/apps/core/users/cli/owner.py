"""Local user administration commands."""

from asyncio import run
from collections.abc import Callable
from typing import cast

import typer
from dishka import AsyncContainer
from papilio.errors.base import APPException
from pydantic import ValidationError
from rich.panel import Panel
from rich.text import Text

from src.apps.core.users.app.commands.owner import OwnerCommand
from src.apps.core.users.domain.dtos.owner import OwnerCreate
from src.shared.cli import CLI

cli = typer.Typer(no_args_is_help=True, help="Manage administrator setup.")


async def _setup(container: AsyncContainer, data: OwnerCreate) -> int:
    """Call the owner command and close its container on the same loop."""
    try:
        async with container() as scope:
            command = await scope.get(OwnerCommand)
            owner = await command.create(data)
    finally:
        await container.close()
    return owner.id


@cli.command()
def owner(ctx: typer.Context) -> None:
    """Create the first administrator and the initial access grants."""
    load = cast(Callable[[], CLI], ctx.obj)
    resources = load()
    console = resources.console
    console.print(
        Panel(
            "Create the first Super Admin",
            title=Text("PapilioVPN", style="title"),
            border_style="accent",
            expand=False,
        )
    )
    try:
        data = OwnerCreate.model_validate(
            {
                "first_name": typer.prompt("First name"),
                "last_name": typer.prompt("Last name"),
                "mobile": typer.prompt("Mobile"),
                "password": typer.prompt(
                    "Password", hide_input=True, confirmation_prompt=True
                ),
            }
        )
        owner_id = run(_setup(resources.container, data))
    except ValidationError:
        console.print("Invalid owner details", style="error")
        raise typer.Exit(2) from None
    except APPException as error:
        console.print(Text(error.message), style="error")
        raise typer.Exit(1) from None
    console.print(
        Panel(
            Text(f"Super Admin #{owner_id} created", style="success"),
            border_style="success",
            expand=False,
        )
    )
