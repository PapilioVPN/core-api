from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddVLESSAccountRequest(_message.Message):
    __slots__ = ("id", "inbound_tag", "email", "uuid")
    ID_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    id: str
    inbound_tag: str
    email: str
    uuid: str
    def __init__(self, id: _Optional[str] = ..., inbound_tag: _Optional[str] = ..., email: _Optional[str] = ..., uuid: _Optional[str] = ...) -> None: ...

class RemoveVLESSAccountRequest(_message.Message):
    __slots__ = ("id", "inbound_tag", "email")
    ID_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    id: str
    inbound_tag: str
    email: str
    def __init__(self, id: _Optional[str] = ..., inbound_tag: _Optional[str] = ..., email: _Optional[str] = ...) -> None: ...

class CountVLESSAccountsRequest(_message.Message):
    __slots__ = ("id", "inbound_tag")
    ID_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    id: str
    inbound_tag: str
    def __init__(self, id: _Optional[str] = ..., inbound_tag: _Optional[str] = ...) -> None: ...

class CountVLESSAccountsResponse(_message.Message):
    __slots__ = ("count",)
    COUNT_FIELD_NUMBER: _ClassVar[int]
    count: int
    def __init__(self, count: _Optional[int] = ...) -> None: ...

class SyncUserRequest(_message.Message):
    __slots__ = ("id", "inbound_tag", "email", "uuid", "flow", "credential", "inbound_tags", "assignments")
    ID_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    FLOW_FIELD_NUMBER: _ClassVar[int]
    CREDENTIAL_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAGS_FIELD_NUMBER: _ClassVar[int]
    ASSIGNMENTS_FIELD_NUMBER: _ClassVar[int]
    id: str
    inbound_tag: str
    email: str
    uuid: str
    flow: str
    credential: Credential
    inbound_tags: _containers.RepeatedScalarFieldContainer[str]
    assignments: _containers.RepeatedCompositeFieldContainer[Assignment]
    def __init__(self, id: _Optional[str] = ..., inbound_tag: _Optional[str] = ..., email: _Optional[str] = ..., uuid: _Optional[str] = ..., flow: _Optional[str] = ..., credential: _Optional[_Union[Credential, _Mapping]] = ..., inbound_tags: _Optional[_Iterable[str]] = ..., assignments: _Optional[_Iterable[_Union[Assignment, _Mapping]]] = ...) -> None: ...

class SyncResult(_message.Message):
    __slots__ = ("outcome", "added", "removed", "failure")
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    ADDED_FIELD_NUMBER: _ClassVar[int]
    REMOVED_FIELD_NUMBER: _ClassVar[int]
    FAILURE_FIELD_NUMBER: _ClassVar[int]
    outcome: str
    added: int
    removed: int
    failure: str
    def __init__(self, outcome: _Optional[str] = ..., added: _Optional[int] = ..., removed: _Optional[int] = ..., failure: _Optional[str] = ...) -> None: ...

class VLESSAccount(_message.Message):
    __slots__ = ("email", "uuid", "flow", "credential", "assignments")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    FLOW_FIELD_NUMBER: _ClassVar[int]
    CREDENTIAL_FIELD_NUMBER: _ClassVar[int]
    ASSIGNMENTS_FIELD_NUMBER: _ClassVar[int]
    email: str
    uuid: str
    flow: str
    credential: Credential
    assignments: _containers.RepeatedCompositeFieldContainer[Assignment]
    def __init__(self, email: _Optional[str] = ..., uuid: _Optional[str] = ..., flow: _Optional[str] = ..., credential: _Optional[_Union[Credential, _Mapping]] = ..., assignments: _Optional[_Iterable[_Union[Assignment, _Mapping]]] = ...) -> None: ...

class VLESSAccounts(_message.Message):
    __slots__ = ("accounts",)
    ACCOUNTS_FIELD_NUMBER: _ClassVar[int]
    accounts: _containers.RepeatedCompositeFieldContainer[VLESSAccount]
    def __init__(self, accounts: _Optional[_Iterable[_Union[VLESSAccount, _Mapping]]] = ...) -> None: ...

class SyncUsersRequest(_message.Message):
    __slots__ = ("id", "inbound_tag", "snapshot", "inbound_tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    inbound_tag: str
    snapshot: VLESSAccounts
    inbound_tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., inbound_tag: _Optional[str] = ..., snapshot: _Optional[_Union[VLESSAccounts, _Mapping]] = ..., inbound_tags: _Optional[_Iterable[str]] = ...) -> None: ...

class UsersChunk(_message.Message):
    __slots__ = ("id", "inbound_tag", "index", "last", "accounts", "inbound_tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    LAST_FIELD_NUMBER: _ClassVar[int]
    ACCOUNTS_FIELD_NUMBER: _ClassVar[int]
    INBOUND_TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    inbound_tag: str
    index: int
    last: bool
    accounts: _containers.RepeatedCompositeFieldContainer[VLESSAccount]
    inbound_tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., inbound_tag: _Optional[str] = ..., index: _Optional[int] = ..., last: _Optional[bool] = ..., accounts: _Optional[_Iterable[_Union[VLESSAccount, _Mapping]]] = ..., inbound_tags: _Optional[_Iterable[str]] = ...) -> None: ...

class Credential(_message.Message):
    __slots__ = ("protocol", "uuid", "flow", "password", "method", "key", "auth", "peer")
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    FLOW_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    METHOD_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    PEER_FIELD_NUMBER: _ClassVar[int]
    protocol: str
    uuid: str
    flow: str
    password: str
    method: str
    key: str
    auth: str
    peer: WireGuardPeer
    def __init__(self, protocol: _Optional[str] = ..., uuid: _Optional[str] = ..., flow: _Optional[str] = ..., password: _Optional[str] = ..., method: _Optional[str] = ..., key: _Optional[str] = ..., auth: _Optional[str] = ..., peer: _Optional[_Union[WireGuardPeer, _Mapping]] = ...) -> None: ...

class WireGuardPeer(_message.Message):
    __slots__ = ("public_key", "pre_shared_key", "allowed_ips", "keep_alive")
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    PRE_SHARED_KEY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_IPS_FIELD_NUMBER: _ClassVar[int]
    KEEP_ALIVE_FIELD_NUMBER: _ClassVar[int]
    public_key: str
    pre_shared_key: str
    allowed_ips: _containers.RepeatedScalarFieldContainer[str]
    keep_alive: int
    def __init__(self, public_key: _Optional[str] = ..., pre_shared_key: _Optional[str] = ..., allowed_ips: _Optional[_Iterable[str]] = ..., keep_alive: _Optional[int] = ...) -> None: ...

class Assignment(_message.Message):
    __slots__ = ("inbound_tag", "credential")
    INBOUND_TAG_FIELD_NUMBER: _ClassVar[int]
    CREDENTIAL_FIELD_NUMBER: _ClassVar[int]
    inbound_tag: str
    credential: Credential
    def __init__(self, inbound_tag: _Optional[str] = ..., credential: _Optional[_Union[Credential, _Mapping]] = ...) -> None: ...
