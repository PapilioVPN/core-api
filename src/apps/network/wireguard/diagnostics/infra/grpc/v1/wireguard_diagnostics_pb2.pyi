import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WireGuardEgressProbe(_message.Message):
    __slots__ = ("reachable", "http_status", "elapsed_nanoseconds", "observed_at")
    REACHABLE_FIELD_NUMBER: _ClassVar[int]
    HTTP_STATUS_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_NANOSECONDS_FIELD_NUMBER: _ClassVar[int]
    OBSERVED_AT_FIELD_NUMBER: _ClassVar[int]
    reachable: bool
    http_status: int
    elapsed_nanoseconds: int
    observed_at: _timestamp_pb2.Timestamp
    def __init__(self, reachable: _Optional[bool] = ..., http_status: _Optional[int] = ..., elapsed_nanoseconds: _Optional[int] = ..., observed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class WireGuardDiagnosticsRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class WireGuardLogEvent(_message.Message):
    __slots__ = ("sequence", "at", "kind")
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    AT_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    sequence: int
    at: _timestamp_pb2.Timestamp
    kind: str
    def __init__(self, sequence: _Optional[int] = ..., at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., kind: _Optional[str] = ...) -> None: ...

class WireGuardRuntimeStats(_message.Message):
    __slots__ = ("goroutines", "gc_count", "heap_bytes", "allocated_bytes", "system_bytes", "allocations", "frees", "live_objects", "gc_pause_nanoseconds", "uptime_seconds")
    GOROUTINES_FIELD_NUMBER: _ClassVar[int]
    GC_COUNT_FIELD_NUMBER: _ClassVar[int]
    HEAP_BYTES_FIELD_NUMBER: _ClassVar[int]
    ALLOCATED_BYTES_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_BYTES_FIELD_NUMBER: _ClassVar[int]
    ALLOCATIONS_FIELD_NUMBER: _ClassVar[int]
    FREES_FIELD_NUMBER: _ClassVar[int]
    LIVE_OBJECTS_FIELD_NUMBER: _ClassVar[int]
    GC_PAUSE_NANOSECONDS_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    goroutines: int
    gc_count: int
    heap_bytes: int
    allocated_bytes: int
    system_bytes: int
    allocations: int
    frees: int
    live_objects: int
    gc_pause_nanoseconds: int
    uptime_seconds: int
    def __init__(self, goroutines: _Optional[int] = ..., gc_count: _Optional[int] = ..., heap_bytes: _Optional[int] = ..., allocated_bytes: _Optional[int] = ..., system_bytes: _Optional[int] = ..., allocations: _Optional[int] = ..., frees: _Optional[int] = ..., live_objects: _Optional[int] = ..., gc_pause_nanoseconds: _Optional[int] = ..., uptime_seconds: _Optional[int] = ...) -> None: ...
