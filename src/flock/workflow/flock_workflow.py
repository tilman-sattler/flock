from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities from the new file
with workflow.unsafe.imports_passed_through():
    from flock.core.context.context import FlockContext
    from flock.core.context.context_vars import FLOCK_CURRENT_AGENT
    from flock.core.flock_router import HandOffRequest
    from flock.core.logging.logging import get_logger
    from flock.workflow.agent_execution_activity import (
        determine_next_agent,
        execute_single_agent,
    )


logger = get_logger("workflow")


@workflow.defn
class FlockWorkflow:
    # No need for __init__ storing context anymore if passed to run

    @workflow.run
    async def run(self, context_dict: dict) -> dict:
        # Deserialize context at the beginning

        context = FlockContext.from_dict(context_dict)
        context.workflow_id = workflow.info().workflow_id
        context.workflow_timestamp = workflow.info().start_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        current_agent_name = context.get_variable(FLOCK_CURRENT_AGENT)
        final_result = None
        previous_agent_name = (
            None  # Keep track of the agent that called the current one
        )

        logger.info(
            "Starting workflow execution",
            workflow_id=context.workflow_id,
            start_time=context.workflow_timestamp,
            initial_agent=current_agent_name,
        )

        try:
            while current_agent_name:
                logger.info(
                    "Executing agent activity", agent=current_agent_name
                )
                # --- Execute the current agent ---
                agent_result = await workflow.execute_activity(
                    execute_single_agent,
                    args=[current_agent_name, context],
                    start_to_close_timeout=timedelta(
                        minutes=5
                    ),  # Adjust timeout as needed
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        non_retryable_error_types=[
                            "ValueError",
                            "TypeError",
                        ],  # Don't retry programmer errors
                    ),
                )

                # Record the execution in the context history
                # Note: The 'called_from' is the agent *before* this one
                context.record(
                    agent_name=current_agent_name,
                    data=agent_result,
                    timestamp=workflow.now().isoformat(),  # Use deterministic workflow time
                    hand_off=None,  # Will be updated if handoff occurs
                    called_from=previous_agent_name,  # Pass the correct previous agent
                )

                final_result = agent_result  # Store the result of the last successful agent

                logger.info(
                    "Determining next agent activity",
                    current_agent=current_agent_name,
                )
                # --- Determine the next agent ---
                handoff_data_dict = await workflow.execute_activity(
                    determine_next_agent,
                    args=[current_agent_name, agent_result, context],
                    start_to_close_timeout=timedelta(
                        minutes=1
                    ),  # Routing should be fast
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        non_retryable_error_types=["ValueError", "TypeError"],
                    ),
                )

                # Update previous agent name for the next loop iteration
                previous_agent_name = current_agent_name

                if handoff_data_dict:
                    logger.debug(
                        "Handoff data received", data=handoff_data_dict
                    )
                    # Deserialize handoff data back into Pydantic model for easier access
                    handoff_request = HandOffRequest.model_validate(
                        handoff_data_dict
                    )

                    # Update context based on handoff overrides
                    if handoff_request.override_context:
                        context.state.update(handoff_request.override_context)
                        logger.info("Context updated based on handoff override")

                    # Update the last record's handoff information
                    if context.history:
                        context.history[-1].hand_off = handoff_data_dict

                    # Set the next agent
                    current_agent_name = handoff_request.next_agent
                    if current_agent_name:
                        context.set_variable(
                            FLOCK_CURRENT_AGENT, current_agent_name
                        )
                        logger.info("Next agent set", agent=current_agent_name)
                    else:
                        logger.info(
                            "Handoff requested termination (no next agent)"
                        )
                        break  # Exit loop if router explicitly returned no next agent

                else:
                    # No handoff data returned (no router or router returned None)
                    logger.info("No handoff occurred, workflow terminating.")
                    current_agent_name = None  # End the loop

            # --- Workflow Completion ---
            logger.success(
                "Workflow completed successfully",
                final_agent=previous_agent_name,
            )
            context.set_variable(
                "flock.result",
                {
                    "result": final_result,  # Return the last agent's result
                    "success": True,
                },
            )
            return final_result  # Return the actual result of the last agent

        except Exception as e:
            # Catch exceptions from activities (e.g., after retries fail)
            # or workflow logic errors
            logger.exception("Workflow execution failed", error=str(e))
            context.set_variable(
                "flock.result",
                {
                    "result": f"Workflow failed: {e}",
                    "success": False,
                },
            )
            # It's often better to let Temporal record the failure status
            # by re-raising the exception rather than returning a custom error dict.
            # However, returning the context might be useful for debugging.
            # Consider re-raising: raise
            return context.model_dump(
                mode="json"
            )  # Return context state on failure
