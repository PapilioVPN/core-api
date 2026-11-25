"""Remove an operator account while protecting the Super Admin."""

from papilio.infra.db.tools.decorators import transactional

from ...domain.models.records import UserModel
from ..interfaces.services import IUserService
from ..validators.profile import protect_owner


class UserRemoveCommand:
    def __init__(self, users: IUserService) -> None:
        """Bind the authoritative account reader and writer."""
        self.users = users

    @transactional
    async def remove(self, id: int) -> UserModel:
        """Remove an account without permitting removal of a Super Admin.

        Args:
            id: Account identity.

        Returns:
            The removed account.

        Raises:
            ForbiddenException: The account is a Super Admin.
            NotFoundException: The account does not exist.
        """
        user = await self.users.get_by_id(id)
        protect_owner(user)
        removed = await self.users.remove(id)
        return removed
