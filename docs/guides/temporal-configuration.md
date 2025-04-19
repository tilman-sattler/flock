# Configuring Temporal Execution

When you run your Flock workflows using Temporal (`enable_temporal=True`), you gain access to powerful features for reliability and scalability. Flock allows you to declaratively configure various Temporal settings for both the overall workflow and individual agent activities.

## Why Configure Temporal?

- **Task Queues:** Route different workflows or agents to specific worker pools (e.g., GPU workers, high-priority workers).
- **Timeouts:** Prevent runaway executions and manage resource usage.
- **Retry Policies:** Automatically handle transient failures (like network issues or temporary API outages) with configurable backoff strategies.

## Prerequisites

- Ensure you have Temporal running and accessible.
- Enable Temporal execution in your Flock: `Flock(enable_temporal=True, ...)`

## Workflow-Level Configuration (`TemporalWorkflowConfig`)

You can define default settings for the entire workflow execution when you initialize your `Flock`.

```python
# Import necessary classes
from datetime import timedelta
from flock.core import Flock
# Adjust path if needed: from flock.config.temporal_config import ...
from flock.workflow.temporal_config import TemporalWorkflowConfig, TemporalRetryPolicyConfig 

# Define a custom retry policy (e.g., fewer retries by default)
default_retry = TemporalRetryPolicyConfig(
    maximum_attempts=2, # Default 2 attempts for activities
    initial_interval=timedelta(seconds=2)
)

# Define workflow configuration
workflow_config = TemporalWorkflowConfig(
    task_queue="my-custom-queue", # Default queue for this Flock's workflows
    workflow_execution_timeout=timedelta(minutes=30), # Max 30 mins total
    default_activity_retry_policy=default_retry
)

# Pass the config to your Flock
my_flock = Flock(
    name="configured_flock",
    enable_temporal=True,
    temporal_config=workflow_config
    # ... other Flock args
)

print(f"Flock configured for Temporal queue: {my_flock.temporal_config.task_queue}") 
```

**Key `TemporalWorkflowConfig` Fields:**

- `task_queue`: The default Temporal Task Queue for this workflow. Workers must listen on this queue.
- `workflow_execution_timeout`: Maximum total duration for the workflow.
- `workflow_run_timeout`: Maximum duration for a single run attempt.
- `default_activity_retry_policy`: A `TemporalRetryPolicyConfig` object defining the default retry behavior for all activities *unless overridden by an agent*.

## Agent-Specific Configuration (`TemporalActivityConfig`)

Sometimes, different agents need different settings (e.g., longer timeouts for complex tasks, different retry logic for external API calls). You can specify these when defining your `FlockAgent`.

```python
# Import necessary classes
from datetime import timedelta
from flock.core import FlockFactory
# Adjust path if needed: from flock.config.temporal_config import ...
from flock.workflow.temporal_config import TemporalActivityConfig, TemporalRetryPolicyConfig 

# Define a specific retry policy for this agent
agent_retry = TemporalRetryPolicyConfig(
    maximum_attempts=5, # Allow more retries
    non_retryable_error_types=["ValueError"] # Don't retry specific errors
)

# Define activity configuration for this agent
agent_activity_config = TemporalActivityConfig(
    start_to_close_timeout=timedelta(minutes=3), # Allow 3 minutes per attempt
    retry_policy=agent_retry,
    task_queue="gpu-workers-queue" # Optionally route this agent to different workers!
)

# Create the agent and pass the config
special_agent = FlockFactory.create_default_agent(
    name="special_gpu_agent",
    input="data",
    output="processed_data",
    # Add the specific Temporal config here!
    temporal_activity_config=agent_activity_config
)

# Assuming 'my_flock' is the Flock instance from the previous example
# my_flock.add_agent(special_agent) 

# You can inspect the agent's config:
print(f"Agent '{special_agent.name}' config timeout: {special_agent.temporal_activity_config.start_to_close_timeout}")
```

**Key `TemporalActivityConfig` Fields:**

- `task_queue`: Route *this specific agent's* execution to a different task queue (overrides workflow default).
- `start_to_close_timeout`: Maximum duration for a single attempt of *this specific agent's* activity.
- `retry_policy`: A `TemporalRetryPolicyConfig` defining retry behavior specifically for *this agent*, overriding the workflow default.

**Configuration Precedence:**

Settings are applied with the following priority:

1.  Agent's `temporal_activity_config` (if set for a specific field)
2.  Flock's `temporal_config.default_activity_retry_policy` (for retries)
3.  Flock's `temporal_config.task_queue` (for activity task queue, if not set on agent)
4.  Temporal's built-in defaults (e.g., for timeouts if not set anywhere).

## Runtime Metadata (`memo`)

You can add non-indexed metadata to your workflow run for observability using the `memo` parameter in `run` or `run_async`:

```python
# Assuming 'my_flock' is the Flock instance from previous examples
# result = my_flock.run_async(
#    start_agent="some_agent",
#    input={"data": "..."},
#    memo={"user_id": "user123", "experiment_tag": "v2-prompt"}
# )
```

This metadata will be visible in the Temporal UI.

## Example

Here's a combined example similar to the one used during development:

```python
# .flock/flock_temporal_config_example.py
import asyncio
from datetime import timedelta

# Import Temporal config models (adjust path if needed)
from flock.workflow.temporal_config import (
    TemporalActivityConfig,
    TemporalRetryPolicyConfig,
    TemporalWorkflowConfig,
)
from flock.core import Flock, FlockFactory
from flock.routers.default.default_router import DefaultRouterConfig

async def main():
    # 1. Define Workflow Config
    workflow_config = TemporalWorkflowConfig(
        task_queue="flock-example-queue", 
        workflow_execution_timeout=timedelta(minutes=10), 
        default_activity_retry_policy=TemporalRetryPolicyConfig(maximum_attempts=2)
    )

    # 2. Create Flock with Temporal Config
    flock = Flock(
        enable_temporal=True, # MUST be True to use Temporal config
        enable_logging=True,
        temporal_config=workflow_config
    )

    # 3. Presentation Agent (uses workflow defaults)
    agent = FlockFactory.create_default_agent(
        name="presentation_agent",
        input="topic",
        output="funny_title, funny_slide_headers",
    )
    flock.add_agent(agent)

    # 4. Content Agent Config (specific settings)
    content_agent_retry = TemporalRetryPolicyConfig(maximum_attempts=4)
    content_agent_activity_config = TemporalActivityConfig(
        start_to_close_timeout=timedelta(minutes=1), 
        retry_policy=content_agent_retry
    )

    # 5. Content Agent (with specific config)
    content_agent = FlockFactory.create_default_agent(
        name="content_agent",
        input="funny_title, funny_slide_headers",
        output="funny_slide_content",
        temporal_activity_config=content_agent_activity_config 
    )
    flock.add_agent(content_agent)

    # 6. Add routing
    agent.add_component(DefaultRouterConfig(hand_off="content_agent"))

    print(f"Starting Flock run on Temporal task queue: {workflow_config.task_queue}")
    print(f"Ensure a Temporal worker is listening on '{workflow_config.task_queue}'")
    
    # 7. Run the workflow (example input)
    try:
        result = await flock.run_async(
            start_agent="presentation_agent",
            input={"topic": "Why Temporal makes distributed systems easier"},
            memo={"run_type": "docs_example"} # Example memo
        )

        print("\n--- Result ---")
        print(result)
    except Exception as e:
        print(f"\n--- An error occurred ---")
        print(f"Error: {e}")
        print("Ensure Temporal service and worker are running correctly.")


if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- Learn more about Temporal's concepts like [Task Queues](https://docs.temporal.io/concepts/what-is-a-task-queue) and [Retries](https://docs.temporal.io/concepts/what-is-a-retry-policy).
- Explore how to run [Temporal Workers](https://docs.temporal.io/application-development/foundations#worker) to process tasks from your queues. 