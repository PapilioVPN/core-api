from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HysteriaInstanceState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HYSTERIA_INSTANCE_STATE_UNSPECIFIED: _ClassVar[HysteriaInstanceState]
    HYSTERIA_INSTANCE_STATE_STOPPED: _ClassVar[HysteriaInstanceState]
    HYSTERIA_INSTANCE_STATE_STARTING: _ClassVar[HysteriaInstanceState]
    HYSTERIA_INSTANCE_STATE_READY: _ClassVar[HysteriaInstanceState]
    HYSTERIA_INSTANCE_STATE_STOPPING: _ClassVar[HysteriaInstanceState]
    HYSTERIA_INSTANCE_STATE_FAILED: _ClassVar[HysteriaInstanceState]

class HysteriaStartAction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HYSTERIA_START_ACTION_UNSPECIFIED: _ClassVar[HysteriaStartAction]
    HYSTERIA_START_ACTION_STARTED: _ClassVar[HysteriaStartAction]
    HYSTERIA_START_ACTION_HEARTBEAT: _ClassVar[HysteriaStartAction]
    HYSTERIA_START_ACTION_RESTARTED: _ClassVar[HysteriaStartAction]
    HYSTERIA_START_ACTION_RECOVERED: _ClassVar[HysteriaStartAction]
HYSTERIA_INSTANCE_STATE_UNSPECIFIED: HysteriaInstanceState
HYSTERIA_INSTANCE_STATE_STOPPED: HysteriaInstanceState
HYSTERIA_INSTANCE_STATE_STARTING: HysteriaInstanceState
HYSTERIA_INSTANCE_STATE_READY: HysteriaInstanceState
HYSTERIA_INSTANCE_STATE_STOPPING: HysteriaInstanceState
HYSTERIA_INSTANCE_STATE_FAILED: HysteriaInstanceState
HYSTERIA_START_ACTION_UNSPECIFIED: HysteriaStartAction
HYSTERIA_START_ACTION_STARTED: HysteriaStartAction
HYSTERIA_START_ACTION_HEARTBEAT: HysteriaStartAction
HYSTERIA_START_ACTION_RESTARTED: HysteriaStartAction
HYSTERIA_START_ACTION_RECOVERED: HysteriaStartAction

class HysteriaInstanceRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class StartHysteriaRequest(_message.Message):
    __slots__ = ("id", "config_yaml")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_YAML_FIELD_NUMBER: _ClassVar[int]
    id: str
    config_yaml: bytes
    def __init__(self, id: _Optional[str] = ..., config_yaml: _Optional[bytes] = ...) -> None: ...

class HysteriaInstanceStatus(_message.Message):
    __slots__ = ("id", "state", "hysteria_version", "node_version", "start_action", "applied_config_sha256")
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    HYSTERIA_VERSION_FIELD_NUMBER: _ClassVar[int]
    NODE_VERSION_FIELD_NUMBER: _ClassVar[int]
    START_ACTION_FIELD_NUMBER: _ClassVar[int]
    APPLIED_CONFIG_SHA256_FIELD_NUMBER: _ClassVar[int]
    id: str
    state: HysteriaInstanceState
    hysteria_version: str
    node_version: str
    start_action: HysteriaStartAction
    applied_config_sha256: str
    def __init__(self, id: _Optional[str] = ..., state: _Optional[_Union[HysteriaInstanceState, str]] = ..., hysteria_version: _Optional[str] = ..., node_version: _Optional[str] = ..., start_action: _Optional[_Union[HysteriaStartAction, str]] = ..., applied_config_sha256: _Optional[str] = ...) -> None: ...
