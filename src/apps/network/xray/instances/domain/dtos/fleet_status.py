"""Typed identities requested by the Xray fleet status view."""

from papilio.schemas.inputs import BaseDTO

from .identity import XrayInstanceTargets


class XrayFleetStatusInput(BaseDTO):
    targets: XrayInstanceTargets
