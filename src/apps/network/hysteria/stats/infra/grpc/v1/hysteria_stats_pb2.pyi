from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HysteriaStatsRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class HysteriaRuntimeStats(_message.Message):
    __slots__ = ("execution", "ready_since_unix_nano", "uptime_seconds")
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    READY_SINCE_UNIX_NANO_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    execution: int
    ready_since_unix_nano: int
    uptime_seconds: int
    def __init__(self, execution: _Optional[int] = ..., ready_since_unix_nano: _Optional[int] = ..., uptime_seconds: _Optional[int] = ...) -> None: ...

class HysteriaTrafficRequest(_message.Message):
    __slots__ = ("id", "user_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    def __init__(self, id: _Optional[str] = ..., user_id: _Optional[str] = ...) -> None: ...

class HysteriaTrafficEntry(_message.Message):
    __slots__ = ("user_id", "tx_bytes", "rx_bytes")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    tx_bytes: int
    rx_bytes: int
    def __init__(self, user_id: _Optional[str] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ...) -> None: ...

class HysteriaTrafficSnapshot(_message.Message):
    __slots__ = ("entries", "reset_scope")
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    RESET_SCOPE_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[HysteriaTrafficEntry]
    reset_scope: str
    def __init__(self, entries: _Optional[_Iterable[_Union[HysteriaTrafficEntry, _Mapping]]] = ..., reset_scope: _Optional[str] = ...) -> None: ...

class HysteriaOnlineDeviceCount(_message.Message):
    __slots__ = ("user_id", "devices")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    devices: int
    def __init__(self, user_id: _Optional[str] = ..., devices: _Optional[int] = ...) -> None: ...

class HysteriaOnlineUsers(_message.Message):
    __slots__ = ("users",)
    USERS_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[HysteriaOnlineDeviceCount]
    def __init__(self, users: _Optional[_Iterable[_Union[HysteriaOnlineDeviceCount, _Mapping]]] = ...) -> None: ...

class DisconnectHysteriaUsersRequest(_message.Message):
    __slots__ = ("id", "user_ids")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_IDS_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., user_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class HysteriaDisconnectResult(_message.Message):
    __slots__ = ("acknowledged",)
    ACKNOWLEDGED_FIELD_NUMBER: _ClassVar[int]
    acknowledged: bool
    def __init__(self, acknowledged: _Optional[bool] = ...) -> None: ...
