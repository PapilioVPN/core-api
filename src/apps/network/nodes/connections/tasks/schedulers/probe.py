"""Run one scheduled batch of node connection checks."""

from dishka import FromDishka
from papilio_tasks.apps.schedulers import TaskRouter

from ...app.pipelines.probe import NodeProbePipeline
from ...domain.results.probe import NodeProbeBatch
from ...infra.broker.config import BrokerConfig
from ...infra.broker.tasks import check_connections

router = TaskRouter()


@router.task(check_connections, schedule=BrokerConfig.probe_schedule)
async def probe(*, pipeline: FromDishka[NodeProbePipeline]) -> NodeProbeBatch:
    """Reserve due nodes and persist their latest observation."""
    result = await pipeline.run()
    return result
