"""Check the gateway's signature against the provider's Node signing format."""

import pytest

from src.apps.shop.crypto.payments.infra.nowpayments.signature import (
    verify_signature,
)

pytestmark = pytest.mark.unit


def test_signature() -> None:
    # Signature generated with the provider's Node signing example.
    body = (
        '{"payment_id":704,"memo":"پرداخت",'
        '"fee":{"serviceFee":1e-7,"depositFee":0.000001,'
        '"currency":"trx","withdrawalFee":0.0},"order_id":"14"}'
    ).encode()
    signature = (
        "ae0c66943f48215dbace00d44e9ed825dce32592d0413fbd32b3755d10b942ee87"
        "cbbbdc35d0d8b0c7cda4aa754f63f9992e1e73bfa567aef1229948a1c659b2"
    )
    assert verify_signature(body, signature, "test-ipn-secret")
    assert not verify_signature(
        body.replace(b"704", b"705"), signature, "test-ipn-secret"
    )
    assert not verify_signature(body, signature, "different-key")
    assert not verify_signature(b'{"price":NaN}', signature, "test-ipn-secret")
