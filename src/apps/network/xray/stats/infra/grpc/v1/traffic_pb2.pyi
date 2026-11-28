from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class XrayTrafficScope(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_TRAFFIC_SCOPE_UNSPECIFIED: _ClassVar[XrayTrafficScope]
    XRAY_TRAFFIC_SCOPE_USER: _ClassVar[XrayTrafficScope]
    XRAY_TRAFFIC_SCOPE_INBOUND: _ClassVar[XrayTrafficScope]
    XRAY_TRAFFIC_SCOPE_OUTBOUND: _ClassVar[XrayTrafficScope]

class XrayTrafficDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_TRAFFIC_DIRECTION_UNSPECIFIED: _ClassVar[XrayTrafficDirection]
    XRAY_TRAFFIC_DIRECTION_UPLINK: _ClassVar[XrayTrafficDirection]
    XRAY_TRAFFIC_DIRECTION_DOWNLINK: _ClassVar[XrayTrafficDirection]
XRAY_TRAFFIC_SCOPE_UNSPECIFIED: XrayTrafficScope
XRAY_TRAFFIC_SCOPE_USER: XrayTrafficScope
XRAY_TRAFFIC_SCOPE_INBOUND: XrayTrafficScope
XRAY_TRAFFIC_SCOPE_OUTBOUND: XrayTrafficScope
XRAY_TRAFFIC_DIRECTION_UNSPECIFIED: XrayTrafficDirection
XRAY_TRAFFIC_DIRECTION_UPLINK: XrayTrafficDirection
XRAY_TRAFFIC_DIRECTION_DOWNLINK: XrayTrafficDirection

class XrayTrafficRequest(_message.Message):
    __slots__ = ("id", "scope", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    scope: XrayTrafficScope
    name: str
    def __init__(self, id: _Optional[str] = ..., scope: _Optional[_Union[XrayTrafficScope, str]] = ..., name: _Optional[str] = ...) -> None: ...

class XrayTrafficListRequest(_message.Message):
    __slots__ = ("id", "scope")
    ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    id: str
    scope: XrayTrafficScope
    def __init__(self, id: _Optional[str] = ..., scope: _Optional[_Union[XrayTrafficScope, str]] = ...) -> None: ...

class XrayTrafficUsage(_message.Message):
    __slots__ = ("name", "uplink_bytes", "downlink_bytes")
    NAME_FIELD_NUMBER: _ClassVar[int]
    UPLINK_BYTES_FIELD_NUMBER: _ClassVar[int]
    DOWNLINK_BYTES_FIELD_NUMBER: _ClassVar[int]
    name: str
    uplink_bytes: int
    downlink_bytes: int
    def __init__(self, name: _Optional[str] = ..., uplink_bytes: _Optional[int] = ..., downlink_bytes: _Optional[int] = ...) -> None: ...

class XrayTrafficList(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[XrayTrafficUsage]
    def __init__(self, entries: _Optional[_Iterable[_Union[XrayTrafficUsage, _Mapping]]] = ...) -> None: ...

class XrayTrafficResetRequest(_message.Message):
    __slots__ = ("id", "scope", "name", "direction")
    ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    id: str
    scope: XrayTrafficScope
    name: str
    direction: XrayTrafficDirection
    def __init__(self, id: _Optional[str] = ..., scope: _Optional[_Union[XrayTrafficScope, str]] = ..., name: _Optional[str] = ..., direction: _Optional[_Union[XrayTrafficDirection, str]] = ...) -> None: ...

class XrayTrafficResetResult(_message.Message):
    __slots__ = ("previous_bytes",)
    PREVIOUS_BYTES_FIELD_NUMBER: _ClassVar[int]
    previous_bytes: int
    def __init__(self, previous_bytes: _Optional[int] = ...) -> None: ...

class XrayTrafficResetFailure(_message.Message):
    __slots__ = ("effect",)
    class Effect(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        EFFECT_UNSPECIFIED: _ClassVar[XrayTrafficResetFailure.Effect]
        NOT_APPLIED: _ClassVar[XrayTrafficResetFailure.Effect]
        UNKNOWN: _ClassVar[XrayTrafficResetFailure.Effect]
    EFFECT_UNSPECIFIED: XrayTrafficResetFailure.Effect
    NOT_APPLIED: XrayTrafficResetFailure.Effect
    UNKNOWN: XrayTrafficResetFailure.Effect
    EFFECT_FIELD_NUMBER: _ClassVar[int]
    effect: XrayTrafficResetFailure.Effect
    def __init__(self, effect: _Optional[_Union[XrayTrafficResetFailure.Effect, str]] = ...) -> None: ...

class XrayTrafficPairResetRequest(_message.Message):
    __slots__ = ("id", "scope", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    scope: XrayTrafficScope
    name: str
    def __init__(self, id: _Optional[str] = ..., scope: _Optional[_Union[XrayTrafficScope, str]] = ..., name: _Optional[str] = ...) -> None: ...

class XrayTrafficPairResetResult(_message.Message):
    __slots__ = ("uplink", "downlink")
    UPLINK_FIELD_NUMBER: _ClassVar[int]
    DOWNLINK_FIELD_NUMBER: _ClassVar[int]
    uplink: XrayTrafficDirectionReset
    downlink: XrayTrafficDirectionReset
    def __init__(self, uplink: _Optional[_Union[XrayTrafficDirectionReset, _Mapping]] = ..., downlink: _Optional[_Union[XrayTrafficDirectionReset, _Mapping]] = ...) -> None: ...

class XrayTrafficDirectionReset(_message.Message):
    __slots__ = ("effect", "previous_bytes")
    class Effect(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        EFFECT_UNSPECIFIED: _ClassVar[XrayTrafficDirectionReset.Effect]
        ACKNOWLEDGED: _ClassVar[XrayTrafficDirectionReset.Effect]
        MISSING: _ClassVar[XrayTrafficDirectionReset.Effect]
        NOT_APPLIED: _ClassVar[XrayTrafficDirectionReset.Effect]
        UNKNOWN: _ClassVar[XrayTrafficDirectionReset.Effect]
        NOT_ATTEMPTED: _ClassVar[XrayTrafficDirectionReset.Effect]
    EFFECT_UNSPECIFIED: XrayTrafficDirectionReset.Effect
    ACKNOWLEDGED: XrayTrafficDirectionReset.Effect
    MISSING: XrayTrafficDirectionReset.Effect
    NOT_APPLIED: XrayTrafficDirectionReset.Effect
    UNKNOWN: XrayTrafficDirectionReset.Effect
    NOT_ATTEMPTED: XrayTrafficDirectionReset.Effect
    EFFECT_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_BYTES_FIELD_NUMBER: _ClassVar[int]
    effect: XrayTrafficDirectionReset.Effect
    previous_bytes: int
    def __init__(self, effect: _Optional[_Union[XrayTrafficDirectionReset.Effect, str]] = ..., previous_bytes: _Optional[int] = ...) -> None: ...

class XrayTrafficScopeResetRequest(_message.Message):
    __slots__ = ("id", "scope", "max_counters")
    ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    MAX_COUNTERS_FIELD_NUMBER: _ClassVar[int]
    id: str
    scope: XrayTrafficScope
    max_counters: int
    def __init__(self, id: _Optional[str] = ..., scope: _Optional[_Union[XrayTrafficScope, str]] = ..., max_counters: _Optional[int] = ...) -> None: ...

class XrayTrafficScopeResetResult(_message.Message):
    __slots__ = ("outcome", "counters")
    class Outcome(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        OUTCOME_UNSPECIFIED: _ClassVar[XrayTrafficScopeResetResult.Outcome]
        COMPLETE: _ClassVar[XrayTrafficScopeResetResult.Outcome]
        INTERRUPTED: _ClassVar[XrayTrafficScopeResetResult.Outcome]
        UNKNOWN: _ClassVar[XrayTrafficScopeResetResult.Outcome]
    OUTCOME_UNSPECIFIED: XrayTrafficScopeResetResult.Outcome
    COMPLETE: XrayTrafficScopeResetResult.Outcome
    INTERRUPTED: XrayTrafficScopeResetResult.Outcome
    UNKNOWN: XrayTrafficScopeResetResult.Outcome
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    COUNTERS_FIELD_NUMBER: _ClassVar[int]
    outcome: XrayTrafficScopeResetResult.Outcome
    counters: _containers.RepeatedCompositeFieldContainer[XrayTrafficScopedCounterReset]
    def __init__(self, outcome: _Optional[_Union[XrayTrafficScopeResetResult.Outcome, str]] = ..., counters: _Optional[_Iterable[_Union[XrayTrafficScopedCounterReset, _Mapping]]] = ...) -> None: ...

class XrayTrafficScopedCounterReset(_message.Message):
    __slots__ = ("name", "direction", "result")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    name: str
    direction: XrayTrafficDirection
    result: XrayTrafficDirectionReset
    def __init__(self, name: _Optional[str] = ..., direction: _Optional[_Union[XrayTrafficDirection, str]] = ..., result: _Optional[_Union[XrayTrafficDirectionReset, _Mapping]] = ...) -> None: ...
