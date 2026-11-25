"""Manage automatic payment policy and the hook key in the panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.commands.key import PaymentKeyCommand
from ...app.interfaces.queries import IPaymentSettingsQuery
from ...app.interfaces.services import IPaymentSettingsService
from ...domain.dtos.records import PaymentSettingsWrite
from ...domain.results.records import PaymentSettingsView
from ..schemas.records import PaymentKeyOutput, PaymentSettingsOutput

router = APIRouter(
    prefix="/admin/payment-settings",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("")
async def get_settings(
    query: FromDishka[IPaymentSettingsQuery],
) -> APIResponse[PaymentSettingsOutput, None]:
    settings = await query.get()
    output = PaymentSettingsOutput.from_obj(settings)
    return APIResponse[PaymentSettingsOutput, None].from_data(output)


@router.put("")
async def put_settings(
    data: PaymentSettingsWrite, service: FromDishka[IPaymentSettingsService]
) -> APIResponse[PaymentSettingsOutput, None]:
    settings = await service.save(data)
    view = PaymentSettingsView.from_record(settings)
    output = PaymentSettingsOutput.from_obj(view)
    return APIResponse[PaymentSettingsOutput, None].from_data(output)


@router.post("/key", status_code=201)
async def post_key(
    response: Response, command: FromDishka[PaymentKeyCommand]
) -> APIResponse[PaymentKeyOutput, None]:
    key = await command.issue()
    response.headers["Cache-Control"] = "no-store"
    return APIResponse[PaymentKeyOutput, None].from_data(
        PaymentKeyOutput(key=key)
    )


@router.delete("/key", status_code=204)
async def delete_key(service: FromDishka[IPaymentSettingsService]) -> Response:
    await service.set_key_hash(None)
    return Response(status_code=204)
