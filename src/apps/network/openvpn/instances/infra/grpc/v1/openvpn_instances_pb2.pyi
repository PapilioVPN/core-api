from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OpenVPNInstanceState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OPEN_VPN_INSTANCE_STATE_UNSPECIFIED: _ClassVar[OpenVPNInstanceState]
    OPEN_VPN_INSTANCE_STATE_STOPPED: _ClassVar[OpenVPNInstanceState]
    OPEN_VPN_INSTANCE_STATE_STARTING: _ClassVar[OpenVPNInstanceState]
    OPEN_VPN_INSTANCE_STATE_READY: _ClassVar[OpenVPNInstanceState]
    OPEN_VPN_INSTANCE_STATE_STOPPING: _ClassVar[OpenVPNInstanceState]
    OPEN_VPN_INSTANCE_STATE_FAILED: _ClassVar[OpenVPNInstanceState]

class OpenVPNStartAction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OPEN_VPN_START_ACTION_UNSPECIFIED: _ClassVar[OpenVPNStartAction]
    OPEN_VPN_START_ACTION_STARTED: _ClassVar[OpenVPNStartAction]
    OPEN_VPN_START_ACTION_HEARTBEAT: _ClassVar[OpenVPNStartAction]
    OPEN_VPN_START_ACTION_RESTARTED: _ClassVar[OpenVPNStartAction]
    OPEN_VPN_START_ACTION_RECOVERED: _ClassVar[OpenVPNStartAction]

class OpenVPNConfigIssueCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OPEN_VPN_CONFIG_ISSUE_CODE_UNSPECIFIED: _ClassVar[OpenVPNConfigIssueCode]
    OPEN_VPN_CONFIG_ISSUE_CODE_INVALID_SOURCE: _ClassVar[OpenVPNConfigIssueCode]
    OPEN_VPN_CONFIG_ISSUE_CODE_UNSUPPORTED_DIRECTIVE: _ClassVar[OpenVPNConfigIssueCode]
    OPEN_VPN_CONFIG_ISSUE_CODE_OPTIONS_REJECTED: _ClassVar[OpenVPNConfigIssueCode]
OPEN_VPN_INSTANCE_STATE_UNSPECIFIED: OpenVPNInstanceState
OPEN_VPN_INSTANCE_STATE_STOPPED: OpenVPNInstanceState
OPEN_VPN_INSTANCE_STATE_STARTING: OpenVPNInstanceState
OPEN_VPN_INSTANCE_STATE_READY: OpenVPNInstanceState
OPEN_VPN_INSTANCE_STATE_STOPPING: OpenVPNInstanceState
OPEN_VPN_INSTANCE_STATE_FAILED: OpenVPNInstanceState
OPEN_VPN_START_ACTION_UNSPECIFIED: OpenVPNStartAction
OPEN_VPN_START_ACTION_STARTED: OpenVPNStartAction
OPEN_VPN_START_ACTION_HEARTBEAT: OpenVPNStartAction
OPEN_VPN_START_ACTION_RESTARTED: OpenVPNStartAction
OPEN_VPN_START_ACTION_RECOVERED: OpenVPNStartAction
OPEN_VPN_CONFIG_ISSUE_CODE_UNSPECIFIED: OpenVPNConfigIssueCode
OPEN_VPN_CONFIG_ISSUE_CODE_INVALID_SOURCE: OpenVPNConfigIssueCode
OPEN_VPN_CONFIG_ISSUE_CODE_UNSUPPORTED_DIRECTIVE: OpenVPNConfigIssueCode
OPEN_VPN_CONFIG_ISSUE_CODE_OPTIONS_REJECTED: OpenVPNConfigIssueCode

class OpenVPNInstanceRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class OpenVPNStartRequest(_message.Message):
    __slots__ = ("id", "config_text")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_TEXT_FIELD_NUMBER: _ClassVar[int]
    id: str
    config_text: bytes
    def __init__(self, id: _Optional[str] = ..., config_text: _Optional[bytes] = ...) -> None: ...

class ValidateOpenVPNConfigRequest(_message.Message):
    __slots__ = ("id", "config_text")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_TEXT_FIELD_NUMBER: _ClassVar[int]
    id: str
    config_text: bytes
    def __init__(self, id: _Optional[str] = ..., config_text: _Optional[bytes] = ...) -> None: ...

class OpenVPNInstanceStatus(_message.Message):
    __slots__ = ("id", "state", "node_version", "start_action", "applied_config_sha256", "openvpn_version", "execution_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    NODE_VERSION_FIELD_NUMBER: _ClassVar[int]
    START_ACTION_FIELD_NUMBER: _ClassVar[int]
    APPLIED_CONFIG_SHA256_FIELD_NUMBER: _ClassVar[int]
    OPENVPN_VERSION_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    state: OpenVPNInstanceState
    node_version: str
    start_action: OpenVPNStartAction
    applied_config_sha256: str
    openvpn_version: str
    execution_id: str
    def __init__(self, id: _Optional[str] = ..., state: _Optional[_Union[OpenVPNInstanceState, str]] = ..., node_version: _Optional[str] = ..., start_action: _Optional[_Union[OpenVPNStartAction, str]] = ..., applied_config_sha256: _Optional[str] = ..., openvpn_version: _Optional[str] = ..., execution_id: _Optional[str] = ...) -> None: ...

class OpenVPNConfigIssue(_message.Message):
    __slots__ = ("code", "line")
    CODE_FIELD_NUMBER: _ClassVar[int]
    LINE_FIELD_NUMBER: _ClassVar[int]
    code: OpenVPNConfigIssueCode
    line: int
    def __init__(self, code: _Optional[_Union[OpenVPNConfigIssueCode, str]] = ..., line: _Optional[int] = ...) -> None: ...

class OpenVPNConfigValidation(_message.Message):
    __slots__ = ("id", "valid", "issue")
    ID_FIELD_NUMBER: _ClassVar[int]
    VALID_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    id: str
    valid: bool
    issue: OpenVPNConfigIssue
    def __init__(self, id: _Optional[str] = ..., valid: _Optional[bool] = ..., issue: _Optional[_Union[OpenVPNConfigIssue, _Mapping]] = ...) -> None: ...

class OpenVPNSession(_message.Message):
    __slots__ = ("id", "common_name", "remote_address", "tunnel_ipv4", "tunnel_ipv6", "rx_bytes", "tx_bytes", "connected_at", "cipher")
    ID_FIELD_NUMBER: _ClassVar[int]
    COMMON_NAME_FIELD_NUMBER: _ClassVar[int]
    REMOTE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_IPV4_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_IPV6_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    CONNECTED_AT_FIELD_NUMBER: _ClassVar[int]
    CIPHER_FIELD_NUMBER: _ClassVar[int]
    id: int
    common_name: str
    remote_address: str
    tunnel_ipv4: str
    tunnel_ipv6: str
    rx_bytes: int
    tx_bytes: int
    connected_at: int
    cipher: str
    def __init__(self, id: _Optional[int] = ..., common_name: _Optional[str] = ..., remote_address: _Optional[str] = ..., tunnel_ipv4: _Optional[str] = ..., tunnel_ipv6: _Optional[str] = ..., rx_bytes: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., connected_at: _Optional[int] = ..., cipher: _Optional[str] = ...) -> None: ...

class OpenVPNSessionReport(_message.Message):
    __slots__ = ("execution_id", "observed_at", "sessions")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    OBSERVED_AT_FIELD_NUMBER: _ClassVar[int]
    SESSIONS_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    observed_at: int
    sessions: _containers.RepeatedCompositeFieldContainer[OpenVPNSession]
    def __init__(self, execution_id: _Optional[str] = ..., observed_at: _Optional[int] = ..., sessions: _Optional[_Iterable[_Union[OpenVPNSession, _Mapping]]] = ...) -> None: ...

class DisconnectOpenVPNSessionRequest(_message.Message):
    __slots__ = ("id", "execution_id", "session_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    execution_id: str
    session_id: int
    def __init__(self, id: _Optional[str] = ..., execution_id: _Optional[str] = ..., session_id: _Optional[int] = ...) -> None: ...

class OpenVPNLogsRequest(_message.Message):
    __slots__ = ("id", "execution_id", "after_sequence")
    ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    AFTER_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    id: str
    execution_id: str
    after_sequence: int
    def __init__(self, id: _Optional[str] = ..., execution_id: _Optional[str] = ..., after_sequence: _Optional[int] = ...) -> None: ...

class OpenVPNLogBatch(_message.Message):
    __slots__ = ("execution_id", "dropped", "entries")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    DROPPED_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    dropped: int
    entries: _containers.RepeatedCompositeFieldContainer[OpenVPNLog]
    def __init__(self, execution_id: _Optional[str] = ..., dropped: _Optional[int] = ..., entries: _Optional[_Iterable[_Union[OpenVPNLog, _Mapping]]] = ...) -> None: ...

class OpenVPNLog(_message.Message):
    __slots__ = ("sequence", "timestamp", "level", "message")
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    sequence: int
    timestamp: int
    level: str
    message: str
    def __init__(self, sequence: _Optional[int] = ..., timestamp: _Optional[int] = ..., level: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ReplaceOpenVPNRevocationRequest(_message.Message):
    __slots__ = ("id", "signed_pem")
    ID_FIELD_NUMBER: _ClassVar[int]
    SIGNED_PEM_FIELD_NUMBER: _ClassVar[int]
    id: str
    signed_pem: bytes
    def __init__(self, id: _Optional[str] = ..., signed_pem: _Optional[bytes] = ...) -> None: ...

class OpenVPNRevocationStatus(_message.Message):
    __slots__ = ("number", "sha256", "next_update", "revoked_count")
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    SHA256_FIELD_NUMBER: _ClassVar[int]
    NEXT_UPDATE_FIELD_NUMBER: _ClassVar[int]
    REVOKED_COUNT_FIELD_NUMBER: _ClassVar[int]
    number: str
    sha256: str
    next_update: int
    revoked_count: int
    def __init__(self, number: _Optional[str] = ..., sha256: _Optional[str] = ..., next_update: _Optional[int] = ..., revoked_count: _Optional[int] = ...) -> None: ...
