"""Coordinate customer receipt registration and its original image."""

from pathlib import Path

from anyio import to_thread
from anyio.abc import ByteReceiveStream
from papilio.errors.exceptions import ValidationException
from papilio.infra.db.transaction import transaction

from src.apps.core.storage.app.interfaces.files import IFileStorage
from src.apps.shop.customers.profiles.app.interfaces.services import (
    IProfileCRUD,
)

from ...domain.dtos.records import ImageType, ReceiptCreate
from ...domain.models.records import ReceiptModel
from ...infra.images import is_image
from ..interfaces.services import IReceiptCRUD

RECEIPTS_PATH = "/admin/receipts"
IMAGES_PATH = f"{RECEIPTS_PATH}/images"


class ReceiptCommand:
    def __init__(
        self,
        profiles: IProfileCRUD,
        receipts: IReceiptCRUD,
        files: IFileStorage,
    ) -> None:
        """Bind receipt registration to its customer and file owners.

        Args:
            profiles: Authoritative customer reads.
            receipts: Receipt record service.
            files: Shared file storage service.

        Returns:
            None.
        """
        self.profiles = profiles
        self.receipts = receipts
        self.files = files

    async def create(
        self,
        customer_id: int,
        data: ReceiptCreate,
        source: ByteReceiveStream,
        *,
        mime_type: ImageType,
    ) -> ReceiptModel:
        """Register a pending receipt after publishing its validated image.

        Args:
            customer_id: Existing customer identity.
            data: Validated positive amount in rials.
            source: Borrowed image stream.
            mime_type: Expected image media type.

        Returns:
            The pending receipt and its protected image address.

        Raises:
            NotFoundException: The customer does not exist.
            ValidationException: The received body is not a valid image.
            FileTooLarge: The storage byte limit was exceeded.
        """
        async with transaction():
            await self.profiles.get_by_id(customer_id)

        async def validate(path: Path) -> None:
            if not await to_thread.run_sync(is_image, path, mime_type):
                raise ValidationException(
                    message="The file is not a valid receipt image.",
                    message_code="receipt_image_invalid",
                    loc=["image"],
                )

        url = await self.files.upload(
            source,
            base_url=IMAGES_PATH,
            suffix=mime_type.split("/", 1)[1],
            validate=validate,
        )
        receipt = await self.receipts.create(
            ReceiptModel(
                customer_id=customer_id, amount=data.amount, image_url=url
            )
        )
        return receipt
