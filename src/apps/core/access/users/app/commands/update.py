"""Apply an operator account edit without deactivating a Super Admin."""

from papilio.infra.db.tools.decorators import transactional

from ...domain.dtos.records import UserUpdate
from ...domain.models.records import UserModel
from ..interfaces.services import IUserService
from ..validators.profile import protect_owner


class UserUpdateCommand:
    def __init__(self, users: IUserService) -> None:
        """Bind the authoritative account reader and writer."""
        self.users = users

    @transactional
    async def update(self, id: int, data: UserUpdate) -> UserModel:
        """Apply a profile patch, protecting the owner on deactivation.

        Args:
            id: Account identity.
            data: Validated profile patch.

        Returns:
            The updated account.

        Raises:
            ForbiddenException: The update deactivates a Super Admin.
            NotFoundException: The account does not exist.
        """
        if data.is_active is False:
            user = await self.users.get_by_id(id)
            protect_owner(user)
        updated = await self.users.update(id, data)
        return updated
