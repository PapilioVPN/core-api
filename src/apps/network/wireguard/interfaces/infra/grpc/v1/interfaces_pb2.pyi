import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WireGuardConfigIssue(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WIRE_GUARD_CONFIG_ISSUE_UNSPECIFIED: _ClassVar[WireGuardConfigIssue]
    WIRE_GUARD_CONFIG_ISSUE_INVALID_JSON: _ClassVar[WireGuardConfigIssue]
    WIRE_GUARD_CONFIG_ISSUE_INVALID_PRIVATE_KEY: _ClassVar[WireGuardConfigIssue]
    WIRE_GUARD_CONFIG_ISSUE_INVALID_ADDRESSES: _ClassVar[WireGuardConfigIssue]
    WIRE_GUARD_CONFIG_ISSUE_DUPLICATE_ADDRESS: _ClassVar[WireGuardConfigIssue]
    WIRE_GUARD_CONFIG_ISSUE_INVALID_MTU: _ClassVar[WireGuardConfigIssue]
    WIRE_GUARD_CONFIG_ISSUE_INVALID_LISTEN_PORT: _ClassVar[WireGuardConfigIssue]
    WIRE_GUARD_CONFIG_ISSUE_INVALID_INITIAL_PEERS: _ClassVar[WireGuardConfigIssue]
WIRE_GUARD_CONFIG_ISSUE_UNSPECIFIED: WireGuardConfigIssue
WIRE_GUARD_CONFIG_ISSUE_INVALID_JSON: WireGuardConfigIssue
WIRE_GUARD_CONFIG_ISSUE_INVALID_PRIVATE_KEY: WireGuardConfigIssue
WIRE_GUARD_CONFIG_ISSUE_INVALID_ADDRESSES: WireGuardConfigIssue
WIRE_GUARD_CONFIG_ISSUE_DUPLICATE_ADDRESS: WireGuardConfigIssue
WIRE_GUARD_CONFIG_ISSUE_INVALID_MTU: WireGuardConfigIssue
WIRE_GUARD_CONFIG_ISSUE_INVALID_LISTEN_PORT: WireGuardConfigIssue
WIRE_GUARD_CONFIG_ISSUE_INVALID_INITIAL_PEERS: WireGuardConfigIssue

class WireGuardPeerMember(_message.Message):
    __slots__ = ("public_key", "allowed_ips")
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_IPS_FIELD_NUMBER: _ClassVar[int]
    public_key: bytes
    allowed_ips: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, public_key: _Optional[bytes] = ..., allowed_ips: _Optional[_Iterable[str]] = ...) -> None: ...

class WireGuardPeerMembership(_message.Message):
    __slots__ = ("peers",)
    PEERS_FIELD_NUMBER: _ClassVar[int]
    peers: _containers.RepeatedCompositeFieldContainer[WireGuardPeerMember]
    def __init__(self, peers: _Optional[_Iterable[_Union[WireGuardPeerMember, _Mapping]]] = ...) -> None: ...

class WireGuardInterfaceRequest(_message.Message):
    __slots__ = ("name", "include_configuration")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    name: str
    include_configuration: bool
    def __init__(self, name: _Optional[str] = ..., include_configuration: _Optional[bool] = ...) -> None: ...

class WireGuardInterfaceStatus(_message.Message):
    __slots__ = ("name", "mtu", "up", "applied_config_sha256", "configuration", "keep_alive_expires_at", "recreated", "node_version", "kernel_release", "wireguard_tools_version", "interface_index")
    NAME_FIELD_NUMBER: _ClassVar[int]
    MTU_FIELD_NUMBER: _ClassVar[int]
    UP_FIELD_NUMBER: _ClassVar[int]
    APPLIED_CONFIG_SHA256_FIELD_NUMBER: _ClassVar[int]
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    KEEP_ALIVE_EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    RECREATED_FIELD_NUMBER: _ClassVar[int]
    NODE_VERSION_FIELD_NUMBER: _ClassVar[int]
    KERNEL_RELEASE_FIELD_NUMBER: _ClassVar[int]
    WIREGUARD_TOOLS_VERSION_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_INDEX_FIELD_NUMBER: _ClassVar[int]
    name: str
    mtu: int
    up: bool
    applied_config_sha256: str
    configuration: WireGuardInterfaceConfiguration
    keep_alive_expires_at: _timestamp_pb2.Timestamp
    recreated: bool
    node_version: str
    kernel_release: str
    wireguard_tools_version: str
    interface_index: int
    def __init__(self, name: _Optional[str] = ..., mtu: _Optional[int] = ..., up: _Optional[bool] = ..., applied_config_sha256: _Optional[str] = ..., configuration: _Optional[_Union[WireGuardInterfaceConfiguration, _Mapping]] = ..., keep_alive_expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., recreated: _Optional[bool] = ..., node_version: _Optional[str] = ..., kernel_release: _Optional[str] = ..., wireguard_tools_version: _Optional[str] = ..., interface_index: _Optional[int] = ...) -> None: ...

class WireGuardInterfaceConfiguration(_message.Message):
    __slots__ = ("public_key", "listen_port", "addresses")
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    LISTEN_PORT_FIELD_NUMBER: _ClassVar[int]
    ADDRESSES_FIELD_NUMBER: _ClassVar[int]
    public_key: bytes
    listen_port: int
    addresses: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, public_key: _Optional[bytes] = ..., listen_port: _Optional[int] = ..., addresses: _Optional[_Iterable[str]] = ...) -> None: ...

class WireGuardStartRequest(_message.Message):
    __slots__ = ("name", "config_json", "keep_alive_seconds")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_JSON_FIELD_NUMBER: _ClassVar[int]
    KEEP_ALIVE_SECONDS_FIELD_NUMBER: _ClassVar[int]
    name: str
    config_json: bytes
    keep_alive_seconds: int
    def __init__(self, name: _Optional[str] = ..., config_json: _Optional[bytes] = ..., keep_alive_seconds: _Optional[int] = ...) -> None: ...

class WireGuardStopResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class WireGuardValidateConfigRequest(_message.Message):
    __slots__ = ("name", "config_json")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_JSON_FIELD_NUMBER: _ClassVar[int]
    name: str
    config_json: bytes
    def __init__(self, name: _Optional[str] = ..., config_json: _Optional[bytes] = ...) -> None: ...

class WireGuardConfigValidation(_message.Message):
    __slots__ = ("valid", "issue")
    VALID_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    issue: WireGuardConfigIssue
    def __init__(self, valid: _Optional[bool] = ..., issue: _Optional[_Union[WireGuardConfigIssue, str]] = ...) -> None: ...

class WireGuardPeer(_message.Message):
    __slots__ = ("public_key", "allowed_ips", "preshared_key")
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_IPS_FIELD_NUMBER: _ClassVar[int]
    PRESHARED_KEY_FIELD_NUMBER: _ClassVar[int]
    public_key: bytes
    allowed_ips: _containers.RepeatedScalarFieldContainer[str]
    preshared_key: bytes
    def __init__(self, public_key: _Optional[bytes] = ..., allowed_ips: _Optional[_Iterable[str]] = ..., preshared_key: _Optional[bytes] = ...) -> None: ...

class WireGuardPeerSet(_message.Message):
    __slots__ = ("peers",)
    PEERS_FIELD_NUMBER: _ClassVar[int]
    peers: _containers.RepeatedCompositeFieldContainer[WireGuardPeer]
    def __init__(self, peers: _Optional[_Iterable[_Union[WireGuardPeer, _Mapping]]] = ...) -> None: ...

class WireGuardSyncPeersRequest(_message.Message):
    __slots__ = ("name", "desired", "reconcile")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESIRED_FIELD_NUMBER: _ClassVar[int]
    RECONCILE_FIELD_NUMBER: _ClassVar[int]
    name: str
    desired: WireGuardPeerSet
    reconcile: bool
    def __init__(self, name: _Optional[str] = ..., desired: _Optional[_Union[WireGuardPeerSet, _Mapping]] = ..., reconcile: _Optional[bool] = ...) -> None: ...

class WireGuardPeerSyncResult(_message.Message):
    __slots__ = ("added", "updated", "removed")
    ADDED_FIELD_NUMBER: _ClassVar[int]
    UPDATED_FIELD_NUMBER: _ClassVar[int]
    REMOVED_FIELD_NUMBER: _ClassVar[int]
    added: int
    updated: int
    removed: int
    def __init__(self, added: _Optional[int] = ..., updated: _Optional[int] = ..., removed: _Optional[int] = ...) -> None: ...

class WireGuardUpsertPeerRequest(_message.Message):
    __slots__ = ("name", "peer")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PEER_FIELD_NUMBER: _ClassVar[int]
    name: str
    peer: WireGuardPeer
    def __init__(self, name: _Optional[str] = ..., peer: _Optional[_Union[WireGuardPeer, _Mapping]] = ...) -> None: ...

class WireGuardRemovePeerRequest(_message.Message):
    __slots__ = ("name", "public_key")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    name: str
    public_key: bytes
    def __init__(self, name: _Optional[str] = ..., public_key: _Optional[bytes] = ...) -> None: ...

class WireGuardRemovePeerResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class WireGuardApplyPeerDeltaRequest(_message.Message):
    __slots__ = ("name", "upsert", "remove")
    NAME_FIELD_NUMBER: _ClassVar[int]
    UPSERT_FIELD_NUMBER: _ClassVar[int]
    REMOVE_FIELD_NUMBER: _ClassVar[int]
    name: str
    upsert: _containers.RepeatedCompositeFieldContainer[WireGuardPeer]
    remove: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, name: _Optional[str] = ..., upsert: _Optional[_Iterable[_Union[WireGuardPeer, _Mapping]]] = ..., remove: _Optional[_Iterable[bytes]] = ...) -> None: ...

class WireGuardPeerDeltaChunk(_message.Message):
    __slots__ = ("name", "index", "last", "upsert", "remove")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    LAST_FIELD_NUMBER: _ClassVar[int]
    UPSERT_FIELD_NUMBER: _ClassVar[int]
    REMOVE_FIELD_NUMBER: _ClassVar[int]
    name: str
    index: int
    last: bool
    upsert: _containers.RepeatedCompositeFieldContainer[WireGuardPeer]
    remove: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, name: _Optional[str] = ..., index: _Optional[int] = ..., last: _Optional[bool] = ..., upsert: _Optional[_Iterable[_Union[WireGuardPeer, _Mapping]]] = ..., remove: _Optional[_Iterable[bytes]] = ...) -> None: ...

class WireGuardPeerStats(_message.Message):
    __slots__ = ("public_key", "rx_bytes", "tx_bytes", "last_handshake")
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    LAST_HANDSHAKE_FIELD_NUMBER: _ClassVar[int]
    public_key: bytes
    rx_bytes: int
    tx_bytes: int
    last_handshake: _timestamp_pb2.Timestamp
    def __init__(self, public_key: _Optional[bytes] = ..., rx_bytes: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., last_handshake: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class WireGuardPeerStatsList(_message.Message):
    __slots__ = ("peers",)
    PEERS_FIELD_NUMBER: _ClassVar[int]
    peers: _containers.RepeatedCompositeFieldContainer[WireGuardPeerStats]
    def __init__(self, peers: _Optional[_Iterable[_Union[WireGuardPeerStats, _Mapping]]] = ...) -> None: ...
