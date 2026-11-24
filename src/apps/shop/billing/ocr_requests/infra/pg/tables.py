"""PostgreSQL records for OCR attempts."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import OCRRequestModel


class OCRRequestTable(OCRRequestModel, BaseTable, table=True):
    pass
