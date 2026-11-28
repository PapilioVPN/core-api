"""Dispatch Stop and explicit revision Restart between SQL phases."""

from papilio.errors.exceptions import NotFoundException

from src.apps.network.xray.validation.app.interfaces.dry_run import (
    IXrayConfigGateway,
)
from src.apps.network.xray.validation.domain.enums.dry_run import (
    XrayValidationStatus,
)

from ...domain.enums.start import (
    XrayExecutionAction,
    XrayStartReason,
    XrayStartState,
)
from ...domain.results.start import XrayStartOutcome, XrayStartTarget
from ..executions.start import XrayStartExecution
from ..interfaces.start import IXrayStartGateway


class XrayControlPipeline:
    def __init__(
        self,
        execution: XrayStartExecution,
        gateway: IXrayStartGateway,
        validation: IXrayConfigGateway,
    ) -> None:
        self.execution = execution
        self.gateway = gateway
        self.validation = validation

    async def run(self, id: int) -> None:
        """Dispatch a committed Stop or Restart once.

        Args:
            id: Persisted operation requested through the control stream.
        """
        target = await self.execution.claim(
            id, (XrayExecutionAction.STOP, XrayExecutionAction.RESTART)
        )
        if target is not None:
            if target.action is XrayExecutionAction.STOP:
                outcome = await self.gateway.stop(target)
            else:
                outcome = await self._restart(id, target)
            await self.execution.finish(id, outcome)

    async def _restart(
        self, id: int, target: XrayStartTarget
    ) -> XrayStartOutcome:
        failure = XrayStartOutcome(
            XrayStartState.FAILED, XrayStartReason.REVISION_UNAVAILABLE
        )
        if target.revision_id is None:
            outcome = failure
        else:
            try:
                source = await self.execution.load_source(target.revision_id)
            except NotFoundException:
                source = None
            if source is None:
                outcome = failure
            else:
                validation = await self.validation.validate(
                    node=target.node,
                    instance_id=target.instance_id,
                    source=source.config_json,
                )
                if validation.status is XrayValidationStatus.VALID:
                    outcome = await self.gateway.stop(target)
                    if outcome.state is XrayStartState.SUCCEEDED:
                        if await self.execution.record_stop(id):
                            applied = await self.gateway.start(
                                target, config_json=source.config_json
                            )
                            outcome = applied.for_digest(source.config_sha256)
                        else:
                            outcome = XrayStartOutcome(
                                XrayStartState.UNKNOWN,
                                XrayStartReason.DISPATCH_EXPIRED,
                            )
                else:
                    reason = (
                        XrayStartReason.REJECTED
                        if validation.status is XrayValidationStatus.INVALID
                        else XrayStartReason.PREFLIGHT_FAILED
                    )
                    outcome = XrayStartOutcome(XrayStartState.FAILED, reason)
        return outcome
