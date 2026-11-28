from src.apps.network.xray.stats.infra.grpc.v1 import traffic_pb2 as _traffic_pb2
from src.apps.network.xray.stats.infra.grpc.v1 import online_pb2 as _online_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class XrayRuntimeStatsRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class XrayRuntimeStats(_message.Message):
    __slots__ = ("goroutines", "gc_count", "heap_allocated_bytes", "total_allocated_bytes", "system_bytes", "mallocs", "frees", "live_objects", "gc_pause_total_nanoseconds", "uptime_seconds")
    GOROUTINES_FIELD_NUMBER: _ClassVar[int]
    GC_COUNT_FIELD_NUMBER: _ClassVar[int]
    HEAP_ALLOCATED_BYTES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ALLOCATED_BYTES_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_BYTES_FIELD_NUMBER: _ClassVar[int]
    MALLOCS_FIELD_NUMBER: _ClassVar[int]
    FREES_FIELD_NUMBER: _ClassVar[int]
    LIVE_OBJECTS_FIELD_NUMBER: _ClassVar[int]
    GC_PAUSE_TOTAL_NANOSECONDS_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    goroutines: int
    gc_count: int
    heap_allocated_bytes: int
    total_allocated_bytes: int
    system_bytes: int
    mallocs: int
    frees: int
    live_objects: int
    gc_pause_total_nanoseconds: int
    uptime_seconds: int
    def __init__(self, goroutines: _Optional[int] = ..., gc_count: _Optional[int] = ..., heap_allocated_bytes: _Optional[int] = ..., total_allocated_bytes: _Optional[int] = ..., system_bytes: _Optional[int] = ..., mallocs: _Optional[int] = ..., frees: _Optional[int] = ..., live_objects: _Optional[int] = ..., gc_pause_total_nanoseconds: _Optional[int] = ..., uptime_seconds: _Optional[int] = ...) -> None: ...
