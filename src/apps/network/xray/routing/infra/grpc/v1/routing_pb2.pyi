from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class XrayRoutingRuleMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_ROUTING_RULE_MODE_UNSPECIFIED: _ClassVar[XrayRoutingRuleMode]
    XRAY_ROUTING_RULE_MODE_APPEND: _ClassVar[XrayRoutingRuleMode]
    XRAY_ROUTING_RULE_MODE_REPLACE: _ClassVar[XrayRoutingRuleMode]
XRAY_ROUTING_RULE_MODE_UNSPECIFIED: XrayRoutingRuleMode
XRAY_ROUTING_RULE_MODE_APPEND: XrayRoutingRuleMode
XRAY_ROUTING_RULE_MODE_REPLACE: XrayRoutingRuleMode

class XrayRoutingRulesRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class XrayRoutingRule(_message.Message):
    __slots__ = ("outbound_tag", "rule_tag")
    OUTBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    RULE_TAG_FIELD_NUMBER: _ClassVar[int]
    outbound_tag: str
    rule_tag: str
    def __init__(self, outbound_tag: _Optional[str] = ..., rule_tag: _Optional[str] = ...) -> None: ...

class XrayRoutingRules(_message.Message):
    __slots__ = ("rules",)
    RULES_FIELD_NUMBER: _ClassVar[int]
    rules: _containers.RepeatedCompositeFieldContainer[XrayRoutingRule]
    def __init__(self, rules: _Optional[_Iterable[_Union[XrayRoutingRule, _Mapping]]] = ...) -> None: ...

class XrayBalancerInfoRequest(_message.Message):
    __slots__ = ("id", "tag")
    ID_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    id: str
    tag: str
    def __init__(self, id: _Optional[str] = ..., tag: _Optional[str] = ...) -> None: ...

class XrayBalancerTargets(_message.Message):
    __slots__ = ("tags",)
    TAGS_FIELD_NUMBER: _ClassVar[int]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tags: _Optional[_Iterable[str]] = ...) -> None: ...

class XrayBalancerInfo(_message.Message):
    __slots__ = ("override_target", "reported_targets")
    OVERRIDE_TARGET_FIELD_NUMBER: _ClassVar[int]
    REPORTED_TARGETS_FIELD_NUMBER: _ClassVar[int]
    override_target: str
    reported_targets: XrayBalancerTargets
    def __init__(self, override_target: _Optional[str] = ..., reported_targets: _Optional[_Union[XrayBalancerTargets, _Mapping]] = ...) -> None: ...

class XrayTestRouteRequest(_message.Message):
    __slots__ = ("id", "inbound_tag", "network", "target_ip", "target_domain", "target_port", "protocol", "user", "attributes")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    TARGET_IP_FIELD_NUMBER: _ClassVar[int]
    TARGET_DOMAIN_FIELD_NUMBER: _ClassVar[int]
    TARGET_PORT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    id: str
    inbound_tag: str
    network: str
    target_ip: str
    target_domain: str
    target_port: int
    protocol: str
    user: str
    attributes: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., inbound_tag: _Optional[str] = ..., network: _Optional[str] = ..., target_ip: _Optional[str] = ..., target_domain: _Optional[str] = ..., target_port: _Optional[int] = ..., protocol: _Optional[str] = ..., user: _Optional[str] = ..., attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class XrayRouteSelection(_message.Message):
    __slots__ = ("outbound_tag", "outbound_group_tags")
    OUTBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    OUTBOUND_GROUP_TAGS_FIELD_NUMBER: _ClassVar[int]
    outbound_tag: str
    outbound_group_tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, outbound_tag: _Optional[str] = ..., outbound_group_tags: _Optional[_Iterable[str]] = ...) -> None: ...

class XrayOverrideBalancerTargetRequest(_message.Message):
    __slots__ = ("id", "tag", "target")
    ID_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    id: str
    tag: str
    target: str
    def __init__(self, id: _Optional[str] = ..., tag: _Optional[str] = ..., target: _Optional[str] = ...) -> None: ...

class XrayAddRoutingRuleRequest(_message.Message):
    __slots__ = ("id", "rule_json", "mode", "confirm_replace")
    ID_FIELD_NUMBER: _ClassVar[int]
    RULE_JSON_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    CONFIRM_REPLACE_FIELD_NUMBER: _ClassVar[int]
    id: str
    rule_json: bytes
    mode: XrayRoutingRuleMode
    confirm_replace: bool
    def __init__(self, id: _Optional[str] = ..., rule_json: _Optional[bytes] = ..., mode: _Optional[_Union[XrayRoutingRuleMode, str]] = ..., confirm_replace: _Optional[bool] = ...) -> None: ...

class XrayRemoveRoutingRuleRequest(_message.Message):
    __slots__ = ("id", "rule_tag")
    ID_FIELD_NUMBER: _ClassVar[int]
    RULE_TAG_FIELD_NUMBER: _ClassVar[int]
    id: str
    rule_tag: str
    def __init__(self, id: _Optional[str] = ..., rule_tag: _Optional[str] = ...) -> None: ...
