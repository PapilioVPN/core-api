"""Match bank reports delivered by JetStream."""

from dishka import FromDishka
from faststream import AckPolicy
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ...app.commands.match import DepositMatchCommand
from ...domain.events.records import DepositReceived
from ...infra.broker.config import BrokerConfig
from ...infra.broker.publishers import deposit_received

router = NatsRouter()


@router.subscriber(
    publisher=deposit_received,
    durable=BrokerConfig.match_durable,
    pull_sub=True,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def match(
    event: DepositReceived, *, command: FromDishka[DepositMatchCommand]
) -> None:
    """Apply the current automatic payment policy to a stored report."""
    await command.match(event.deposit_id)
