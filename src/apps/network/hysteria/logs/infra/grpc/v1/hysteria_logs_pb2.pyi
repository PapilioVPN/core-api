from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HysteriaLogsRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class HysteriaLogEvent(_message.Message):
    __slots__ = ("execution", "sequence", "received_unix_nano", "event")
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    RECEIVED_UNIX_NANO_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    execution: int
    sequence: int
    received_unix_nano: int
    event: str
    def __init__(self, execution: _Optional[int] = ..., sequence: _Optional[int] = ..., received_unix_nano: _Optional[int] = ..., event: _Optional[str] = ...) -> None: ...
