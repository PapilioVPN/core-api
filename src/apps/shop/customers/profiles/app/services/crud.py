"""Register and update retail customer profiles."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import ProfileCreate, ProfileUpdate
from ...domain.models.records import CustomerModel
from ...infra.pg.repositories.crud import ProfileRepository


class ProfileCRUD(IDChecks[CustomerModel]):
    entity = "Customer"

    def __init__(self, repo: ProfileRepository) -> None:
        """Bind the request's customer repository.

        Args:
            repo: Native PostgreSQL profile repository.

        Returns:
            None.
        """
        self.repo = repo

    @transactional
    async def create(self, data: ProfileCreate) -> CustomerModel:
        """Register a customer profile in the panel.

        Args:
            data: Validated name, contact details, note and block state.

        Returns:
            The profile with its new customer identity.
        """
        profile = await self.repo.create(
            CustomerModel(
                name=data.name,
                mobile=data.mobile,
                note=data.note,
                is_blocked=data.is_blocked,
            )
        )
        return profile

    async def get_by_id(self, id: int) -> CustomerModel:
        """Read a profile by customer identity.

        Args:
            id: Stored customer identity.

        Returns:
            The requested profile, including blocked profiles.

        Raises:
            NotFoundException: The customer is absent.
        """
        profile = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, profile)

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[CustomerModel]:
        """Read customer profiles through one bounded native selection.

        Args:
            ids: Stored customer identities.

        Returns:
            Unique profile matches, omitting missing identities.
        """
        profiles = await self.repo.get_by_ids(ids) if ids else []
        return profiles

    @transactional
    async def update(self, id: int, data: ProfileUpdate) -> CustomerModel:
        """Apply supplied profile changes.

        Args:
            id: Stored customer identity.
            data: Validated changes; explicit null clears mobile or note.

        Returns:
            The updated profile.

        Raises:
            NotFoundException: The customer is absent.
            ValidationException: The patch has no recognized fields.
        """
        changes = self._check_not_empty_dict(data.to_row())
        profile = await self.repo.update_by_id(id, changes)
        return self._check_for_id_existence(id, profile)
