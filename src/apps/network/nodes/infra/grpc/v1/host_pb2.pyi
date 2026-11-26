import datetime

from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MemorySnapshot(_message.Message):
    __slots__ = ("total_bytes", "available_bytes", "swap_total_bytes", "swap_free_bytes", "used_bytes")
    TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_BYTES_FIELD_NUMBER: _ClassVar[int]
    SWAP_TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    SWAP_FREE_BYTES_FIELD_NUMBER: _ClassVar[int]
    USED_BYTES_FIELD_NUMBER: _ClassVar[int]
    total_bytes: int
    available_bytes: int
    swap_total_bytes: int
    swap_free_bytes: int
    used_bytes: int
    def __init__(self, total_bytes: _Optional[int] = ..., available_bytes: _Optional[int] = ..., swap_total_bytes: _Optional[int] = ..., swap_free_bytes: _Optional[int] = ..., used_bytes: _Optional[int] = ...) -> None: ...

class CPUSnapshot(_message.Message):
    __slots__ = ("busy_percent", "steal_percent", "window_milliseconds", "observed_at")
    BUSY_PERCENT_FIELD_NUMBER: _ClassVar[int]
    STEAL_PERCENT_FIELD_NUMBER: _ClassVar[int]
    WINDOW_MILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    OBSERVED_AT_FIELD_NUMBER: _ClassVar[int]
    busy_percent: float
    steal_percent: float
    window_milliseconds: int
    observed_at: _timestamp_pb2.Timestamp
    def __init__(self, busy_percent: _Optional[float] = ..., steal_percent: _Optional[float] = ..., window_milliseconds: _Optional[int] = ..., observed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class StorageSnapshot(_message.Message):
    __slots__ = ("path", "total_bytes", "used_bytes", "available_bytes", "read_only")
    PATH_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    USED_BYTES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_BYTES_FIELD_NUMBER: _ClassVar[int]
    READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    path: str
    total_bytes: int
    used_bytes: int
    available_bytes: int
    read_only: bool
    def __init__(self, path: _Optional[str] = ..., total_bytes: _Optional[int] = ..., used_bytes: _Optional[int] = ..., available_bytes: _Optional[int] = ..., read_only: _Optional[bool] = ...) -> None: ...

class SystemSnapshot(_message.Message):
    __slots__ = ("uptime_seconds", "cpu", "memory", "storage", "logical_cpu_count", "network")
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    STORAGE_FIELD_NUMBER: _ClassVar[int]
    LOGICAL_CPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    uptime_seconds: int
    cpu: CPUSnapshot
    memory: MemorySnapshot
    storage: StorageSnapshot
    logical_cpu_count: int
    network: NetworkSnapshot
    def __init__(self, uptime_seconds: _Optional[int] = ..., cpu: _Optional[_Union[CPUSnapshot, _Mapping]] = ..., memory: _Optional[_Union[MemorySnapshot, _Mapping]] = ..., storage: _Optional[_Union[StorageSnapshot, _Mapping]] = ..., logical_cpu_count: _Optional[int] = ..., network: _Optional[_Union[NetworkSnapshot, _Mapping]] = ...) -> None: ...

class NetworkSnapshot(_message.Message):
    __slots__ = ("rx_bytes_per_second", "tx_bytes_per_second", "window_milliseconds", "observed_at")
    RX_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    WINDOW_MILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    OBSERVED_AT_FIELD_NUMBER: _ClassVar[int]
    rx_bytes_per_second: int
    tx_bytes_per_second: int
    window_milliseconds: int
    observed_at: _timestamp_pb2.Timestamp
    def __init__(self, rx_bytes_per_second: _Optional[int] = ..., tx_bytes_per_second: _Optional[int] = ..., window_milliseconds: _Optional[int] = ..., observed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
