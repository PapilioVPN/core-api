"""Operator inputs and the persisted, discriminated routing intent."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    StringConstraints,
    TypeAdapter,
)

from ..enums.operation import RoutingAction
from .identity import RoutingTag
from .validators.rule import require_confirmation, require_rule_object

type RoutingRuleJSON = Annotated[
    str,
    StringConstraints(min_length=1, max_length=32 << 10),
    AfterValidator(require_rule_object),
]


class RoutingRuleInput(BaseDTO):
    rule_json: RoutingRuleJSON = Field(repr=False)


class RoutingReplacementInput(RoutingRuleInput):
    confirm_replace: Annotated[
        Literal[True], BeforeValidator(require_confirmation)
    ]


class RoutingOverrideInput(BaseDTO):
    target: RoutingTag


class AppendRule(BaseDTO):
    action: Literal[RoutingAction.APPEND] = RoutingAction.APPEND
    rule: RoutingRuleInput


class ReplaceRules(BaseDTO):
    action: Literal[RoutingAction.REPLACE] = RoutingAction.REPLACE
    rule: RoutingReplacementInput


class RemoveRule(BaseDTO):
    action: Literal[RoutingAction.REMOVE] = RoutingAction.REMOVE
    tag: RoutingTag


class SetBalancer(BaseDTO):
    action: Literal[RoutingAction.OVERRIDE] = RoutingAction.OVERRIDE
    tag: RoutingTag
    override: RoutingOverrideInput


class ClearBalancer(BaseDTO):
    action: Literal[RoutingAction.CLEAR] = RoutingAction.CLEAR
    tag: RoutingTag


type RoutingIntent = Annotated[
    AppendRule | ReplaceRules | RemoveRule | SetBalancer | ClearBalancer,
    Field(discriminator="action"),
]

intent_adapter: TypeAdapter[RoutingIntent] = TypeAdapter(RoutingIntent)
