"""Receive authenticated reports from the bank sender."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from fastapi.security import APIKeyHeader
from papilio.api.responses.envelope import APIResponse

from ...app.commands.records import DepositCommand
from ...domain.dtos.records import DepositCreate
from ..schemas.records import DepositOutput

router = APIRouter(prefix="/hooks/deposits", route_class=DishkaRoute)
key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@router.post("", status_code=201)
async def post_deposit(
    data: DepositCreate,
    key: Annotated[str | None, Depends(key_header)],
    command: FromDishka[DepositCommand],
) -> APIResponse[DepositOutput, None]:
    record = await command.receive(data, key)
    output = DepositOutput.from_obj(record)
    return APIResponse[DepositOutput, None].from_data(output)
