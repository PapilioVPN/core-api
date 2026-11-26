import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from src.apps.network.engines.xray.infra.grpc.v1 import accounts_pb2 as _accounts_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class XrayInstanceState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_INSTANCE_STATE_UNSPECIFIED: _ClassVar[XrayInstanceState]
    XRAY_INSTANCE_STATE_STOPPED: _ClassVar[XrayInstanceState]
    XRAY_INSTANCE_STATE_STARTING: _ClassVar[XrayInstanceState]
    XRAY_INSTANCE_STATE_READY: _ClassVar[XrayInstanceState]
    XRAY_INSTANCE_STATE_STOPPING: _ClassVar[XrayInstanceState]
    XRAY_INSTANCE_STATE_FAILED: _ClassVar[XrayInstanceState]

class XrayStartAction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_START_ACTION_UNSPECIFIED: _ClassVar[XrayStartAction]
    XRAY_START_ACTION_STARTED: _ClassVar[XrayStartAction]
    XRAY_START_ACTION_HEARTBEAT: _ClassVar[XrayStartAction]
    XRAY_START_ACTION_RESTARTED: _ClassVar[XrayStartAction]
    XRAY_START_ACTION_RECOVERED: _ClassVar[XrayStartAction]
    XRAY_START_ACTION_LIVE_UPDATED: _ClassVar[XrayStartAction]
    XRAY_START_ACTION_RESTARTED_AFTER_LIVE_FAILURE: _ClassVar[XrayStartAction]
    XRAY_START_ACTION_LIVE_UPDATE_FAILED: _ClassVar[XrayStartAction]

class XrayStartFailureReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_START_FAILURE_REASON_UNSPECIFIED: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_LAUNCH_FAILED: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_EXITED_BEFORE_READY: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_READINESS_TIMEOUT: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_READINESS_FAILED: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_CONFIG_REJECTED: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_CONFIG_CHECK_FAILED: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_INITIAL_ACCOUNTS_FAILED: _ClassVar[XrayStartFailureReason]
    XRAY_START_FAILURE_REASON_LIVE_APPLY_FAILED: _ClassVar[XrayStartFailureReason]
XRAY_INSTANCE_STATE_UNSPECIFIED: XrayInstanceState
XRAY_INSTANCE_STATE_STOPPED: XrayInstanceState
XRAY_INSTANCE_STATE_STARTING: XrayInstanceState
XRAY_INSTANCE_STATE_READY: XrayInstanceState
XRAY_INSTANCE_STATE_STOPPING: XrayInstanceState
XRAY_INSTANCE_STATE_FAILED: XrayInstanceState
XRAY_START_ACTION_UNSPECIFIED: XrayStartAction
XRAY_START_ACTION_STARTED: XrayStartAction
XRAY_START_ACTION_HEARTBEAT: XrayStartAction
XRAY_START_ACTION_RESTARTED: XrayStartAction
XRAY_START_ACTION_RECOVERED: XrayStartAction
XRAY_START_ACTION_LIVE_UPDATED: XrayStartAction
XRAY_START_ACTION_RESTARTED_AFTER_LIVE_FAILURE: XrayStartAction
XRAY_START_ACTION_LIVE_UPDATE_FAILED: XrayStartAction
XRAY_START_FAILURE_REASON_UNSPECIFIED: XrayStartFailureReason
XRAY_START_FAILURE_REASON_LAUNCH_FAILED: XrayStartFailureReason
XRAY_START_FAILURE_REASON_EXITED_BEFORE_READY: XrayStartFailureReason
XRAY_START_FAILURE_REASON_READINESS_TIMEOUT: XrayStartFailureReason
XRAY_START_FAILURE_REASON_READINESS_FAILED: XrayStartFailureReason
XRAY_START_FAILURE_REASON_CONFIG_REJECTED: XrayStartFailureReason
XRAY_START_FAILURE_REASON_CONFIG_CHECK_FAILED: XrayStartFailureReason
XRAY_START_FAILURE_REASON_INITIAL_ACCOUNTS_FAILED: XrayStartFailureReason
XRAY_START_FAILURE_REASON_LIVE_APPLY_FAILED: XrayStartFailureReason

class XrayInstanceRequest(_message.Message):
    __slots__ = ("id", "config_json", "initial_users", "exclude_inbounds", "keep_alive_seconds")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_JSON_FIELD_NUMBER: _ClassVar[int]
    INITIAL_USERS_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_INBOUNDS_FIELD_NUMBER: _ClassVar[int]
    KEEP_ALIVE_SECONDS_FIELD_NUMBER: _ClassVar[int]
    id: str
    config_json: bytes
    initial_users: _containers.RepeatedCompositeFieldContainer[XrayInitialInboundUsers]
    exclude_inbounds: _containers.RepeatedScalarFieldContainer[str]
    keep_alive_seconds: int
    def __init__(self, id: _Optional[str] = ..., config_json: _Optional[bytes] = ..., initial_users: _Optional[_Iterable[_Union[XrayInitialInboundUsers, _Mapping]]] = ..., exclude_inbounds: _Optional[_Iterable[str]] = ..., keep_alive_seconds: _Optional[int] = ...) -> None: ...

class XrayInitialInboundUsers(_message.Message):
    __slots__ = ("inbound_tag", "accounts")
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    ACCOUNTS_FIELD_NUMBER: _ClassVar[int]
    inbound_tag: str
    accounts: _containers.RepeatedCompositeFieldContainer[XrayInitialAccount]
    def __init__(self, inbound_tag: _Optional[str] = ..., accounts: _Optional[_Iterable[_Union[XrayInitialAccount, _Mapping]]] = ...) -> None: ...

class XrayInitialAccount(_message.Message):
    __slots__ = ("email", "uuid", "credential")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    CREDENTIAL_FIELD_NUMBER: _ClassVar[int]
    email: str
    uuid: str
    credential: _accounts_pb2.Credential
    def __init__(self, email: _Optional[str] = ..., uuid: _Optional[str] = ..., credential: _Optional[_Union[_accounts_pb2.Credential, _Mapping]] = ...) -> None: ...

class XrayInstanceStatus(_message.Message):
    __slots__ = ("id", "state", "xray_version", "node_version", "start_action", "keep_alive_expires_at", "applied_config_sha256")
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    XRAY_VERSION_FIELD_NUMBER: _ClassVar[int]
    NODE_VERSION_FIELD_NUMBER: _ClassVar[int]
    START_ACTION_FIELD_NUMBER: _ClassVar[int]
    KEEP_ALIVE_EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    APPLIED_CONFIG_SHA256_FIELD_NUMBER: _ClassVar[int]
    id: str
    state: XrayInstanceState
    xray_version: str
    node_version: str
    start_action: XrayStartAction
    keep_alive_expires_at: _timestamp_pb2.Timestamp
    applied_config_sha256: str
    def __init__(self, id: _Optional[str] = ..., state: _Optional[_Union[XrayInstanceState, str]] = ..., xray_version: _Optional[str] = ..., node_version: _Optional[str] = ..., start_action: _Optional[_Union[XrayStartAction, str]] = ..., keep_alive_expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., applied_config_sha256: _Optional[str] = ...) -> None: ...

class XrayStartFailure(_message.Message):
    __slots__ = ("reason", "exit_code", "status")
    REASON_FIELD_NUMBER: _ClassVar[int]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    reason: XrayStartFailureReason
    exit_code: int
    status: XrayInstanceStatus
    def __init__(self, reason: _Optional[_Union[XrayStartFailureReason, str]] = ..., exit_code: _Optional[int] = ..., status: _Optional[_Union[XrayInstanceStatus, _Mapping]] = ...) -> None: ...
