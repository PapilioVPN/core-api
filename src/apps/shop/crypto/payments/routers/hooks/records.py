"""Receive authenticated crypto payment notifications from the gateway."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Header, HTTPException, Request, Response
from papilio.errors.exceptions import UnAuthorizedException
from papilio.types.aliases import IdType

from ...app.interfaces.commands import ICryptoPaymentCommand

router = APIRouter(prefix="/hooks/crypto-payments", route_class=DishkaRoute)


@router.post("/{id:int}", status_code=204)
async def post_notification(
    id: IdType,
    request: Request,
    command: FromDishka[ICryptoPaymentCommand],
    signature: Annotated[str | None, Header(alias="x-nowpayments-sig")] = None,
) -> Response:
    if signature is None:
        raise UnAuthorizedException(
            "Invalid payment notification.", "invalid_crypto_ipn"
        )
    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > 64 * 1024:
            raise HTTPException(
                status_code=413, detail="Payment notification is too large."
            )
        payload.extend(chunk)
    await command.receive(id, bytes(payload), signature)
    return Response(status_code=204)
