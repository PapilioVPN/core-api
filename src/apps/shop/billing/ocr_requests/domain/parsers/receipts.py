"""Extract explicit bank receipt fields from recognized text lines."""

from collections.abc import Sequence
from re import compile

from papilio.types.constants import INT64_MAX

from src.apps.shop.billing.receipts.domain.results.extraction import (
    ReceiptFields,
)

DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩يك‌", "01234567890123456789یک ")
AMOUNT = compile(
    r"مبلغ(?:\s+(?:پرداختی|تراکنش|واریزی))?\s*[:：]?\s*"
    r"([0-9]{1,19}|[0-9]{1,3}(?:[,٬][0-9]{3}){1,6})\s*(ریال|تومان)"
)
TRACKING = compile(
    r"(?:کد|شماره)\s+(?:رهگیری|پیگیری)\s*[:：]?\s*([0-9]{1,55})"
)
REFERENCE = compile(r"(?:کد|شماره)\s+مرجع\s*[:：]?\s*([0-9]{1,55})")


def fields(lines: Sequence[str]) -> ReceiptFields:
    """Return unambiguous labeled values, leaving unsupported values absent."""
    amounts: set[int] = set()
    tracking: set[str] = set()
    references: set[str] = set()
    for line in lines:
        text = " ".join(line.translate(DIGITS).split())
        if amount := AMOUNT.fullmatch(text):
            value, unit = amount.groups()
            rials = int(value.replace(",", "").replace("٬", ""))
            if unit == "تومان":
                rials *= 10
            if 0 < rials <= INT64_MAX:
                amounts.add(rials)
        if code := TRACKING.fullmatch(text):
            tracking.add(code[1])
        if code := REFERENCE.fullmatch(text):
            references.add(code[1])
    return ReceiptFields(
        amount=amounts.pop() if len(amounts) == 1 else None,
        tracking_code=tracking.pop() if len(tracking) == 1 else None,
        reference_code=references.pop() if len(references) == 1 else None,
    )
