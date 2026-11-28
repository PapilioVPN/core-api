"""Verify real delivery from a bank hook through automatic confirmation."""

from asyncio import create_subprocess_exec, sleep, timeout, wait_for
from contextlib import AsyncExitStack
from datetime import timedelta
from json import dumps, loads
from os import environ
from pathlib import Path
from sys import executable
from typing import cast

import pytest
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from nats import connect
from nats.errors import TimeoutError as NatsTimeout
from papilio.infra.db.transaction import transaction
from papilio.utils.dates import utc_now

from src.apps.finance.card_to_card.api_keys.app.interfaces.services import (
    IAPIKeyService,
)
from src.apps.finance.card_to_card.api_keys.domain.dtos.records import (
    APIKeyCreate,
)
from src.apps.finance.card_to_card.api_keys.infra.pg.repositories.crud import (
    APIKeyRepository,
)
from src.apps.finance.card_to_card.payments.app.interfaces import commands
from src.apps.finance.card_to_card.payments.domain.dtos.records import (
    AutoPaymentCreate,
)
from src.apps.finance.card_to_card.payments.domain.enums.records import (
    PaymentStatus,
)
from src.apps.finance.card_to_card.payments.infra.broker.config import (
    BrokerConfig as PaymentBroker,
)
from src.apps.finance.card_to_card.payments.infra.pg.repositories.crud import (
    CardPaymentRepository,
)
from src.apps.finance.card_to_card.settings.app.interfaces.cache import (
    ITransferSettingsCache,
)
from src.apps.finance.card_to_card.settings.app.interfaces.services import (
    ITransferSettingsService,
)
from src.apps.finance.card_to_card.settings.domain.dtos.records import (
    TransferSettingsWrite,
)
from src.apps.finance.card_to_card.settings.domain.enums.records import (
    SettingsKey,
)
from src.apps.finance.card_to_card.settings.infra.pg.repositories.crud import (
    TransferSettingsRepository,
)
from src.apps.finance.card_to_card.transfers.infra.broker.config import (
    BrokerConfig as TransferBroker,
)
from src.apps.finance.card_to_card.transfers.infra.pg.repositories import (
    crud as transfer_records,
)
from src.apps.shop.banking.banks.domain.models.records import BankModel
from src.apps.shop.banking.banks.infra.pg.repositories.records import (
    BankRepository,
)
from src.apps.shop.banking.payment_cards.domain.models.records import (
    PaymentCardModel,
)
from src.apps.shop.banking.payment_cards.infra.pg.repositories.crud import (
    PaymentCardRepository,
)
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig

pytestmark = pytest.mark.integration


async def test_transfer_subscriber(
    app: FastAPI, client: AsyncClient, pg: CoreSettings, tmp_path: Path
) -> None:
    url = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not url:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to an isolated JetStream")
    pg.nats = NatsConfig(servers=[url])
    config = tmp_path / "relay.yml"
    config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))
    container = cast(AsyncContainer, app.state.dishka_container)
    number = "0000000000000034"

    async with container() as scope:
        banks = await scope.get(BankRepository)
        cards = await scope.get(PaymentCardRepository)
        async with transaction():
            bank = await banks.create(
                BankModel(code="finance_event", title="Finance Event Test")
            )
            card = await cards.create(
                PaymentCardModel(
                    bank_id=bank.id,
                    card_number=number,
                    holder_name="Test Card",
                    allow_auto=True,
                )
            )
            bank_id, card_id = bank.id, card.id
        keys = await scope.get(IAPIKeyService)
        key = await keys.create(
            APIKeyCreate(
                title="Bank Feed",
                expires_at=utc_now() + timedelta(minutes=30),
            )
        )
        key_id = key.api_key.id
        settings = await scope.get(ITransferSettingsService)
        setting = await settings.save(
            SettingsKey.GENERAL,
            TransferSettingsWrite(
                auto_confirm=True, digits=4, window_minutes=30
            ),
        )
        setting_id = setting.id
        issue = await scope.get(commands.IAutoPaymentCommand)
        payment = await issue.create(
            AutoPaymentCreate(card_id=card_id, amount=120_000)
        )
        payment_id, payable = payment.id, payment.payable_amount

    transfer_id: int | None = None
    try:
        worker = create_events(pg)
        async with AsyncExitStack() as stack:
            stack.push_async_callback(worker.stop)
            await worker.start()
            connection = await connect(url)
            stack.push_async_callback(connection.close)
            relay = await create_subprocess_exec(
                str(Path(executable).with_name("faststream")),
                "run",
                "src.entrypoints.outbox:app",
                env={**environ, "PAPILIO_CONFIG": str(config)},
            )

            async def stop_relay() -> None:
                if relay.returncode is None:
                    relay.terminate()
                    try:
                        await wait_for(relay.wait(), timeout=5)
                    except TimeoutError:
                        relay.kill()
                        await relay.wait()

            stack.push_async_callback(stop_relay)
            jetstream = connection.jetstream()
            outcomes = await jetstream.pull_subscribe(
                PaymentBroker.confirmed, stream=PaymentBroker.stream.name
            )
            reply = await client.post(
                "/hooks/card-to-card/transfers",
                headers={"X-API-Key": key.key},
                json={
                    "amount": payable,
                    "card_number": number,
                    "transferred_at": utc_now().isoformat(),
                },
            )
            assert reply.status_code == 201, reply.text
            transfer_id = reply.json()["data"]["id"]
            (message,) = await outcomes.fetch(1, timeout=12)
            assert loads(message.data) == {"payment_id": payment_id}
            await message.ack()

            duplicate = await jetstream.publish(
                TransferBroker.created,
                dumps({"transfer_id": transfer_id}).encode(),
            )
            async with timeout(5):
                while True:
                    info = await jetstream.consumer_info(
                        duplicate.stream, PaymentBroker.transfer_durable
                    )
                    if (
                        info.ack_floor is not None
                        and info.ack_floor.stream_seq >= duplicate.seq
                    ):
                        break
                    await sleep(0.05)
            with pytest.raises(NatsTimeout):
                await outcomes.fetch(1, timeout=2)

            async with container() as scope:
                payments = await scope.get(CardPaymentRepository)
                stored = await payments.get_by_id(payment_id)
                assert stored is not None
                assert stored.status is PaymentStatus.CONFIRMED
                assert stored.transfer_id == transfer_id
    finally:
        async with container() as scope:
            payments = await scope.get(CardPaymentRepository)
            transfers = await scope.get(transfer_records.TransferRepository)
            keys = await scope.get(APIKeyRepository)
            settings = await scope.get(TransferSettingsRepository)
            cache = await scope.get(ITransferSettingsCache)
            cards = await scope.get(PaymentCardRepository)
            banks = await scope.get(BankRepository)
            async with transaction():
                await payments.remove_by_id(payment_id)
                if transfer_id is not None:
                    await transfers.remove_by_id(transfer_id)
                await cards.remove_by_id(card_id)
                await banks.remove_by_id(bank_id)
                await keys.remove_by_id(key_id)
                await settings.remove_by_id(setting_id)
            await cache.forget(SettingsKey.GENERAL)
