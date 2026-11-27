"""Encode and decode the credentials stored by gateway accounts."""

from papilio.security.crypto import decrypt, encrypt
from pydantic import JsonValue, ValidationError

from ...domain.dtos.configs import ConfigWrite, NowPaymentsConfig, PlisioConfig
from ...domain.models.configs import GatewayConfigModel
from ...domain.results.configs import ConfigFailure, plisio_currency

_SAMPLE_KEY = "replace-with-private-encryption-key"


def encode(
    data: ConfigWrite, key: str
) -> dict[str, JsonValue] | ConfigFailure:
    """Encrypt credentials for storage or report unavailable encryption."""
    result: dict[str, JsonValue] | ConfigFailure = ConfigFailure.UNAVAILABLE
    if key.strip() and key != _SAMPLE_KEY:
        try:
            config: dict[str, JsonValue] = {
                "api_url": data.api_url,
                "api_key": encrypt(data.api_key.get_secret_value(), key),
            }
            if data.kind == "nowpayments":
                config["ipn_secret"] = encrypt(
                    data.ipn_secret.get_secret_value(), key
                )
                if data.callback_url is not None:
                    config["callback_url"] = str(data.callback_url)
            else:
                config["price_currency"] = data.price_currency
        except ValueError:
            pass
        else:
            result = config
    return result


def decode_plisio(
    record: GatewayConfigModel | None, key: str
) -> PlisioConfig | ConfigFailure:
    """Read Plisio credentials without leaking invalid stored data."""
    result: PlisioConfig | ConfigFailure = ConfigFailure.UNAVAILABLE
    if record is not None:
        secret = record.config.get("api_key")
        currency = plisio_currency(record)
        if (
            isinstance(secret, str)
            and secret
            and not isinstance(currency, ConfigFailure)
        ):
            try:
                result = PlisioConfig.model_validate(
                    {
                        "kind": "plisio",
                        "api_url": record.config.get("api_url"),
                        "api_key": decrypt(secret, key),
                        "price_currency": currency,
                    }
                )
            except (ValidationError, ValueError):
                pass
    return result


def decode_nowpayments(
    record: GatewayConfigModel | None, key: str
) -> NowPaymentsConfig | ConfigFailure | None:
    """Distinguish absent NOWPayments settings from unreadable credentials."""
    result: NowPaymentsConfig | ConfigFailure | None = None
    if record is not None and "ipn_secret" in record.config:
        data = record.config
        api_key, secret = data.get("api_key"), data.get("ipn_secret")
        result = ConfigFailure.UNAVAILABLE
        if isinstance(api_key, str) and isinstance(secret, str):
            try:
                result = NowPaymentsConfig.model_validate(
                    {
                        "kind": "nowpayments",
                        "api_url": data.get("api_url"),
                        "callback_url": data.get("callback_url"),
                        "api_key": decrypt(api_key, key),
                        "ipn_secret": decrypt(secret, key),
                    }
                )
            except (ValidationError, ValueError):
                pass
    return result
