from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ValidateHysteriaConfigRequest(_message.Message):
    __slots__ = ("id", "config_yaml")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_YAML_FIELD_NUMBER: _ClassVar[int]
    id: str
    config_yaml: bytes
    def __init__(self, id: _Optional[str] = ..., config_yaml: _Optional[bytes] = ...) -> None: ...

class HysteriaConfigValidation(_message.Message):
    __slots__ = ("id", "valid", "scope", "issue")
    ID_FIELD_NUMBER: _ClassVar[int]
    VALID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    id: str
    valid: bool
    scope: str
    issue: str
    def __init__(self, id: _Optional[str] = ..., valid: _Optional[bool] = ..., scope: _Optional[str] = ..., issue: _Optional[str] = ...) -> None: ...
