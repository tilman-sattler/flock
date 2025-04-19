# src/your_package/core/execution/temporal_executor.py

from flock.core.context.context import FlockContext
from flock.core.context.context_vars import FLOCK_RUN_ID
from flock.core.logging.logging import get_logger
from flock.workflow.agent_execution_activity import (
    determine_next_agent,
    execute_single_agent,
)
from flock.workflow.temporal_setup import create_temporal_client, setup_worker

logger = get_logger("flock")


async def run_temporal_workflow(
    context: FlockContext,
    box_result: bool = True,
) -> dict:
    """Execute the agent workflow via Temporal for robust, distributed processing.

    Args:
        context: The FlockContext instance with state and history.
        box_result: If True, wraps the result in a Box for nicer display.

    Returns:
        A dictionary containing the workflow result.
    """
    try:
        from flock.workflow.flock_workflow import (
            FlockWorkflow,  # Your workflow class
        )

        logger.info("Setting up Temporal worker with granular activities")
        await setup_worker(
            workflow=FlockWorkflow,
            activities=[execute_single_agent, determine_next_agent],
        )
        logger.debug("Creating Temporal client")
        flock_client = await create_temporal_client()
        workflow_id = context.get_variable(FLOCK_RUN_ID)
        logger.info("Executing Temporal workflow", workflow_id=workflow_id)
        context_dict = context.model_dump()
        result = await flock_client.execute_workflow(
            FlockWorkflow.run,
            context_dict,
            id=workflow_id,
            task_queue="flock-queue",
        )

        agent_name = context.get_variable("FLOCK_CURRENT_AGENT")
        logger.debug("Formatting Temporal result", agent=agent_name)

        if box_result:
            from box import Box

            logger.debug("Boxing Temporal result")
            return Box(result)
        return result
    except Exception as e:
        logger.error("Error executing Temporal workflow", error=e)
        raise e
