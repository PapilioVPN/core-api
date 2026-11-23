"""Shared token operations; account authentication stays with its owner."""

from typing import Protocol

from src.apps.core.tokens.domain.models.tokens import (
    TokenIdentity,
    VerifiedToken,
)
from src.apps.core.tokens.domain.results.records import TokenPair


class ITokenService(Protocol):
    async def issue(self, identity: TokenIdentity) -> TokenPair:
        """Issue access and refresh credentials for an authorized identity.

        Args:
            identity: Trusted subject, audience and owner-built claims.
                The caller has already checked account eligibility.

        Returns:
            Credentials and their actual absolute UTC-aware expirations.
            Signing configuration and lifetimes belong to configuration;
            issuance does not itself create or validate a session.
        """
        ...

    async def verify_access(
        self, token: str, *, audience: str
    ) -> VerifiedToken:
        """Verify an access credential for the owning consumer.

        Args:
            token: Untrusted encoded token; never log its value.
            audience: Expected consumer selected by the owning application.

        Returns:
            Materialized identity and verified token timestamps/identity.

        Raises:
            UnAuthorizedException: Signature, expiry, audience, required claims
                or access-token kind is invalid.
        """
        ...

    async def verify_refresh(
        self, token: str, *, audience: str
    ) -> VerifiedToken:
        """Verify a refresh credential without issuing replacement tokens.

        Args:
            token: Untrusted encoded refresh token; never log its value.
            audience: Expected consumer selected by the owning application.

        Returns:
            Materialized identity and verified token timestamps/identity.
            Refresh rotation and account/session checks are separate policies.

        Raises:
            UnAuthorizedException: Signature, expiry, audience, required claims
                or refresh-token kind is invalid.
        """
        ...
