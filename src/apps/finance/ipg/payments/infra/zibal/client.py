"""Issue and verify payments with the Zibal SDK engine."""

from payment_gateways_sdk import (
    ConfigurationError,
    GatewayError,
    PaymentError,
    PaymentInquiry,
    PaymentInquiryStatus,
    PaymentRequest,
    PaymentVerification,
    ZibalAsync,
)
from payment_gateways_sdk.gateways.zibal.constants import REQUEST_SUCCESS_CODE

from ...domain.enums.records import LinkStatus
from ...domain.results.link import LinkRequest, ProviderLink
from ...domain.results.verify import Verification


class ZibalClient:
    async def create(self, request: LinkRequest) -> ProviderLink:
        """Issue a redirect for the stored rial amount using the SDK."""
        result = ProviderLink(LinkStatus.UNKNOWN)
        try:
            gateway = ZibalAsync(
                merchant=request.merchant_id.get_secret_value()
            )
            issued = await gateway.make_payment_request(
                PaymentRequest(
                    amount=request.amount,
                    callback_url=request.callback_url,
                    order_id=str(request.payment_id),
                    description=request.description,
                )
            )
        except ConfigurationError:
            result = ProviderLink(LinkStatus.UNAVAILABLE)
        except GatewayError as error:
            if error.code is not None and error.code != REQUEST_SUCCESS_CODE:
                result = ProviderLink(LinkStatus.REJECTED)
        except PaymentError:
            pass
        else:
            result = ProviderLink(
                LinkStatus.READY, issued.authority, issued.redirect_url
            )
        return result

    async def verify(self, request: Verification) -> str | None:
        """Return the bank reference only when the SDK attests settlement."""
        gateway = ZibalAsync(merchant=request.merchant_id.get_secret_value())
        data = PaymentVerification(
            authority=request.reference,
            amount=request.amount,
            order_id=str(request.id),
        )
        inquiry = await gateway.inquire_payment(
            PaymentInquiry(data.authority, data.amount, data.order_id)
        )
        code = None
        if inquiry.status is PaymentInquiryStatus.VERIFIED:
            code = inquiry.reference
        elif inquiry.status is PaymentInquiryStatus.PAID_UNVERIFIED:
            result = await gateway.verify_payment(data)
            if result.success:
                code = result.reference
        return code
