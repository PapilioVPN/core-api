"""Extract explicit bank receipt fields from recognized text lines."""

from collections.abc import Sequence
from re import Pattern, compile

from papilio.types.constants import INT64_MAX

from src.apps.shop.billing.receipts.domain.results.extraction import (
    ReceiptFields,
)


class ReceiptParser:
    def __init__(self) -> None:
        """Compile the receipt patterns once for reuse across extractions."""
        self.digits = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩يك‌", "01234567890123456789یک "
        )
        self.separators = str.maketrans("", "", ",،٬")
        label = r"مبلغ(?:\s+(?:پرداختی|تراکنش|واریزی|انتقال))?\s*[:：]?"
        value = r"(?:[0-9]{1,19}|[0-9]{1,3}(?:[,،٬][0-9]{3}){1,6})"
        unit = r"ریال|تومان"
        self.label = compile(label)
        self.money = compile(
            rf"(?:(?P<label>{label})\s*)?"
            rf"(?:(?P<value>{value})\s*(?P<unit>{unit})|"
            rf"(?P<unit_first>{unit})\s*(?P<value_last>{value}))"
        )
        self.tracking = compile(
            r"(?:کد|شماره)\s+(?:رهگیری|پیگیری)\s*[:：]?\s*([0-9]{1,55})"
        )
        self.reference = compile(
            r"(?:کد|شماره)\s+مرجع\s*[:：]?\s*([0-9]{1,55})"
        )

    def parse(self, lines: Sequence[str]) -> ReceiptFields:
        """Extract unambiguous values from recognized receipt text.

        Args:
            lines: Ordered OCR text with blanks for low-confidence lines.

        Returns:
            Receipt fields with missing or ambiguous values left unset.
        """
        texts = [
            " ".join(line.translate(self.digits).split()) for line in lines
        ]
        return ReceiptFields(
            amount=self._amount(texts),
            tracking_code=self._code(texts, self.tracking),
            reference_code=self._code(texts, self.reference),
        )

    def _amount(self, texts: Sequence[str]) -> int | None:
        """Read a single labeled amount in rials or leave it unset."""
        labels = {
            index
            for index, text in enumerate(texts)
            if self.label.fullmatch(text)
        }
        amounts: set[int] = set()
        for index, text in enumerate(texts):
            money = self.money.fullmatch(text)
            if money and (
                money["label"] or index - 1 in labels or index + 1 in labels
            ):
                value = money["value"] or money["value_last"]
                unit = money["unit"] or money["unit_first"]
                rials = int(value.translate(self.separators))
                if unit == "تومان":
                    rials *= 10
                if 0 < rials <= INT64_MAX:
                    amounts.add(rials)
        return amounts.pop() if len(amounts) == 1 else None

    @staticmethod
    def _code(texts: Sequence[str], pattern: Pattern[str]) -> str | None:
        """Read a distinct labeled code, preserving leading zeros."""
        codes = {
            match[1] for text in texts if (match := pattern.fullmatch(text))
        }
        return codes.pop() if len(codes) == 1 else None
