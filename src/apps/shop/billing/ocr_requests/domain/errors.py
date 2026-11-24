"""Safe failure codes for an OCR attempt."""


class OCRFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
