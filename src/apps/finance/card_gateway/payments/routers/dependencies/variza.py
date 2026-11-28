"""Read the signed webhook bytes and headers at the HTTP boundary."""

from http import HTTPStatus
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Header, HTTPException, Request
from papilio.types.aliases import IdType

from ...app.interfaces.webhook import IVarizaWebhookService
from ...domain.dtos.paid import PaidDelivery

_MAX_BODY_BYTES = 16 * 1024


@inject
async def read_variza_delivery(
    gateway_id: IdType,
    request: Request,
    webhooks: FromDishka[IVarizaWebhookService],
    delivery_id: Annotated[
        str, Header(alias="X-Delivery-Id", min_length=1, max_length=255)
    ],
    signature: Annotated[
        str | None, Header(alias="X-Webhook-Signature")
    ] = None,
) -> PaidDelivery | None:
    """Pass the bounded signed body and validated headers to the service."""
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > _MAX_BODY_BYTES:
            raise HTTPException(
                status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE
            )
        body.extend(chunk)
    delivery = await webhooks.read(
        gateway_id, delivery_id, bytes(body), signature
    )
    return delivery
