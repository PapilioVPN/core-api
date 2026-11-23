"""Native validated inputs for user account operations."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    IdType,
    MobileType,
    MStrType,
    PageType,
    PasswordType,
    PerPageType,
    ValueType,
)
from pydantic import EmailStr, Field
from pydantic_core import MISSING


class UserCreate(BaseDTO):
    """Account input with optional raw password for command-owned hashing."""

    first_name: MStrType
    last_name: MStrType
    mobile: MobileType
    email: EmailStr | None = Field(default=None, max_length=100)
    role_id: IdType
    is_active: bool = True
    password: PasswordType | None = Field(default=None, repr=False)


class UserUpdate(BaseDTO):
    first_name: MStrType | MISSING = MISSING
    last_name: MStrType | MISSING = MISSING
    mobile: MobileType | MISSING = MISSING
    email: EmailStr | None = Field(default=None, max_length=100)
    is_active: bool | MISSING = MISSING


class UserRoleUpdate(BaseDTO):
    role_id: IdType


class UserBatchRead(BaseDTO):
    ids: list[IdType] = Field(min_length=1, max_length=100)


class UserList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    role_id: IdType | None = None
    is_active: bool | None = None
