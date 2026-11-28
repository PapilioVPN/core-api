from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class XrayOutboundHealthStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_OUTBOUND_HEALTH_STATUS_UNSPECIFIED: _ClassVar[XrayOutboundHealthStatus]
    XRAY_OUTBOUND_HEALTH_STATUS_HEALTHY: _ClassVar[XrayOutboundHealthStatus]
    XRAY_OUTBOUND_HEALTH_STATUS_FAILED: _ClassVar[XrayOutboundHealthStatus]
    XRAY_OUTBOUND_HEALTH_STATUS_NO_SAMPLE: _ClassVar[XrayOutboundHealthStatus]
XRAY_OUTBOUND_HEALTH_STATUS_UNSPECIFIED: XrayOutboundHealthStatus
XRAY_OUTBOUND_HEALTH_STATUS_HEALTHY: XrayOutboundHealthStatus
XRAY_OUTBOUND_HEALTH_STATUS_FAILED: XrayOutboundHealthStatus
XRAY_OUTBOUND_HEALTH_STATUS_NO_SAMPLE: XrayOutboundHealthStatus

class XrayOutboundHealthRequest(_message.Message):
    __slots__ = ("id", "tag")
    ID_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    id: str
    tag: str
    def __init__(self, id: _Optional[str] = ..., tag: _Optional[str] = ...) -> None: ...

class XrayOutboundObservation(_message.Message):
    __slots__ = ("tag", "status", "delay_milliseconds", "last_seen_unix_seconds", "last_try_unix_seconds")
    TAG_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DELAY_MILLISECONDS_FIELD_NUMBER: _ClassVar[int]
    LAST_SEEN_UNIX_SECONDS_FIELD_NUMBER: _ClassVar[int]
    LAST_TRY_UNIX_SECONDS_FIELD_NUMBER: _ClassVar[int]
    tag: str
    status: XrayOutboundHealthStatus
    delay_milliseconds: int
    last_seen_unix_seconds: int
    last_try_unix_seconds: int
    def __init__(self, tag: _Optional[str] = ..., status: _Optional[_Union[XrayOutboundHealthStatus, str]] = ..., delay_milliseconds: _Optional[int] = ..., last_seen_unix_seconds: _Optional[int] = ..., last_try_unix_seconds: _Optional[int] = ...) -> None: ...

class XrayOutboundHealth(_message.Message):
    __slots__ = ("observations",)
    OBSERVATIONS_FIELD_NUMBER: _ClassVar[int]
    observations: _containers.RepeatedCompositeFieldContainer[XrayOutboundObservation]
    def __init__(self, observations: _Optional[_Iterable[_Union[XrayOutboundObservation, _Mapping]]] = ...) -> None: ...
