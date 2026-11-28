from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class XrayLogSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_LOG_SOURCE_UNSPECIFIED: _ClassVar[XrayLogSource]
    XRAY_LOG_SOURCE_STDOUT: _ClassVar[XrayLogSource]
    XRAY_LOG_SOURCE_STDERR: _ClassVar[XrayLogSource]
XRAY_LOG_SOURCE_UNSPECIFIED: XrayLogSource
XRAY_LOG_SOURCE_STDOUT: XrayLogSource
XRAY_LOG_SOURCE_STDERR: XrayLogSource

class XrayLogsRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class XrayLogEvent(_message.Message):
    __slots__ = ("execution", "sequence", "source", "received_unix_nano", "message", "truncated")
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    RECEIVED_UNIX_NANO_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    execution: int
    sequence: int
    source: XrayLogSource
    received_unix_nano: int
    message: bytes
    truncated: bool
    def __init__(self, execution: _Optional[int] = ..., sequence: _Optional[int] = ..., source: _Optional[_Union[XrayLogSource, str]] = ..., received_unix_nano: _Optional[int] = ..., message: _Optional[bytes] = ..., truncated: _Optional[bool] = ...) -> None: ...
