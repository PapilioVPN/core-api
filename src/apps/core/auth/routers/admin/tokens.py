"""Administrator password login through the shared application contract."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Request
from papilio.api.responses.envelope import APIResponse

from src.apps.core.auth.app.interfaces.services import (
    IPasswordLoginService,
)
from src.apps.core.auth.domain.dtos.password import PasswordLogin
from src.apps.core.auth.routers.schemas.tokens import TokenPairOutput

router = APIRouter(
    prefix="/admin/auth/tokens",
    route_class=DishkaRoute,
)


@router.post("", response_model=APIResponse[TokenPairOutput, None])
async def post_tokens(
    data: PasswordLogin,
    request: Request,
    service: FromDishka[IPasswordLoginService],
) -> APIResponse[TokenPairOutput, None]:
    """Issue administrator credentials after password authentication.

    Args:
        data: Mobile and private raw password validated by native input types.
        request: Native request carrying an optional client label.
        service: Request-scoped account eligibility and credential issuer.

    Returns:
        Access/refresh credentials and actual UTC-aware expirations.

    Raises:
        UnAuthorizedException: Credentials or account/role eligibility failed.
        Exception: Backend, hashing or signing failure propagates.
    """
    agent = request.headers.get("user-agent", "")[:255] or None
    result = await service.login(data, user_agent=agent)
    output = TokenPairOutput.from_obj(result)
    return APIResponse[TokenPairOutput, None].from_data(output)
