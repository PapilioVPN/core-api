"""Receive authenticated crypto payment notifications from the gateway."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Header, HTTPException, Request, Response
from papilio.errors.exceptions import UnAuthorizedException
from papilio.types.aliases import IdType

from ...app.interfaces.commands import ICryptoPaymentCommand

router = APIRouter(prefix="/hooks/crypto-payments", route_class=DishkaRoute)


async def _payload(request: Request) -> bytes:
    """Read the signed bytes without buffering an unbounded body."""
    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > 64 * 1024:
            raise HTTPException(
                status_code=413, detail="Payment notification is too large."
            )
        payload.extend(chunk)
    return bytes(payload)


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
    body = await _payload(request)
    await command.receive(id, body, signature)
    return Response(status_code=204)


@router.post("/plisio/{id:int}")
async def post_plisio(
    id: IdType, request: Request, command: FromDishka[ICryptoPaymentCommand]
) -> Response:
    body = await _payload(request)
    await command.receive(id, body)
    return Response(status_code=200)
