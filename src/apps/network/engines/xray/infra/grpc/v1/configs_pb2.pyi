from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class XrayConfigIssueCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XRAY_CONFIG_ISSUE_CODE_UNSPECIFIED: _ClassVar[XrayConfigIssueCode]
    XRAY_CONFIG_ISSUE_CODE_CONFIG_DECODE_ERROR: _ClassVar[XrayConfigIssueCode]
    XRAY_CONFIG_ISSUE_CODE_CONFIG_REJECTED: _ClassVar[XrayConfigIssueCode]
XRAY_CONFIG_ISSUE_CODE_UNSPECIFIED: XrayConfigIssueCode
XRAY_CONFIG_ISSUE_CODE_CONFIG_DECODE_ERROR: XrayConfigIssueCode
XRAY_CONFIG_ISSUE_CODE_CONFIG_REJECTED: XrayConfigIssueCode

class ValidateXrayConfigRequest(_message.Message):
    __slots__ = ("id", "config_json")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_JSON_FIELD_NUMBER: _ClassVar[int]
    id: str
    config_json: bytes
    def __init__(self, id: _Optional[str] = ..., config_json: _Optional[bytes] = ...) -> None: ...

class XrayConfigValidationIssue(_message.Message):
    __slots__ = ("code", "line", "column")
    CODE_FIELD_NUMBER: _ClassVar[int]
    LINE_FIELD_NUMBER: _ClassVar[int]
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    code: XrayConfigIssueCode
    line: int
    column: int
    def __init__(self, code: _Optional[_Union[XrayConfigIssueCode, str]] = ..., line: _Optional[int] = ..., column: _Optional[int] = ...) -> None: ...

class XrayConfigValidation(_message.Message):
    __slots__ = ("id", "valid", "issue")
    ID_FIELD_NUMBER: _ClassVar[int]
    VALID_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    id: str
    valid: bool
    issue: XrayConfigValidationIssue
    def __init__(self, id: _Optional[str] = ..., valid: _Optional[bool] = ..., issue: _Optional[_Union[XrayConfigValidationIssue, _Mapping]] = ...) -> None: ...
