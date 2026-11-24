"""Prepare account creation through role ownership and native hashing."""

from papilio.infra.db.tools.decorators import transactional
from papilio.security.passwords import PasswordHasher

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.users.app.interfaces.services import IUserService
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.core.access.users.domain.models.records import UserModel


class UserCreateCommand:
    def __init__(
        self, users: IUserService, roles: IRoleService, hasher: PasswordHasher
    ) -> None:
        """Bind account persistence, authoritative roles and native hashing.

        Args:
            users: User service on the current request's UoW.
            roles: Role existence contract on that same UoW.
            hasher: Native password hasher with its configured pepper.

        Returns:
            None.
        """
        self.users = users
        self.roles = roles
        self.hasher = hasher

    @transactional
    async def create(
        self, data: UserCreate, *, super_admin: bool = False
    ) -> UserModel:
        """Create an account after password and role preparation.

        Args:
            data: Validated account fields; absent or null password
                skips hashing.
            super_admin: Trusted privilege selected by first-owner setup.

        Returns:
            The stored account, with a native hash or None when no password
            was supplied. No caller-supplied identity or hash is accepted.

        Raises:
            NotFoundException: The referenced role is absent.
            ConflictException: The mobile already belongs to an account.
        """
        hashed_password: str | None = None
        if data.password is not None:
            hashed_password = await self.hasher.hash(data.password)
        await self.roles.get_by_id(data.role_id)
        user = await self.users.create(
            UserModel(
                first_name=data.first_name,
                last_name=data.last_name,
                mobile=data.mobile,
                email=data.email,
                role_id=data.role_id,
                is_active=data.is_active,
                is_super_admin=super_admin,
                hashed_password=hashed_password,
            )
        )
        return user
