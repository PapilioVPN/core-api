"""Pass committed transfer identities to card payment confirmation."""

from dishka import FromDishka
from faststream import AckPolicy
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ....transfers.domain.events.records import TransferCreated
from ....transfers.infra.broker.publishers import transfer_created
from ...app.interfaces.commands import IConfirmTransferCommand
from ...infra.broker.config import BrokerConfig

router = NatsRouter()


@router.subscriber(
    publisher=transfer_created,
    durable=BrokerConfig.transfer_durable,
    pull_sub=True,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def confirm_transfer(
    event: TransferCreated, *, command: FromDishka[IConfirmTransferCommand]
) -> None:
    """Run the payment command before acknowledging the delivery."""
    await command.confirm(event.transfer_id)
