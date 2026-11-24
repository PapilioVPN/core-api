"""Native boto3 sessions and transports for explicit connections."""

from boto3.session import Session
from botocore.config import Config

from src.apps.core.storage.providers.domain.dtos.configs import S3Config


def s3_session(config: S3Config) -> Session:
    """Build a private SDK session without using its shared default session.

    Args:
        config: Explicit validated credentials and optional region.
    Returns:
        A per-operation native session; callers create and close its client.
    """
    session = Session(
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        aws_session_token=config.aws_session_token,
        region_name=config.region_name,
    )
    return session


def s3_transport(config: S3Config) -> Config:
    """Configure bounded native requests for S3-compatible endpoints.

    Args:
        config: Explicit native addressing preference.
    Returns:
        SigV4 transport with finite timeouts and standard SDK retries. Optional
        checksum trailers are disabled; required protocol checks remain native.
    """
    transport = Config(
        signature_version="s3v4",
        connect_timeout=10,
        read_timeout=30,
        retries={"mode": "standard", "total_max_attempts": 3},
        s3={"addressing_style": config.addressing_style},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    )
    return transport
