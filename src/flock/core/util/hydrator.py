# src/flock/util/hydrator.py (Revised - Simpler)

import asyncio
import json
from typing import (
    Any,
    TypeVar,
    get_type_hints,
)

from pydantic import BaseModel

# Import necessary Flock components
from flock.core import Flock, FlockFactory
from flock.core.logging.logging import get_logger

# Import helper to format type hints back to strings
from flock.core.serialization.serialization_utils import _format_type_to_string

logger = get_logger("hydrator")
T = TypeVar("T", bound=BaseModel)


def flockclass(
    model: str = "openai/gpt-4o", agent_description: str | None = None
):
    """Decorator to add a .hydrate() method to a Pydantic class.
    Leverages a dynamic Flock agent to fill missing (None) fields.

    Args:
        model: The default LLM model identifier to use for hydration.
        agent_description: An optional description for the dynamically created agent.
    """

    def decorator(cls: type[T]) -> type[T]:
        if not issubclass(cls, BaseModel):
            raise TypeError(
                "@flockclass can only decorate Pydantic BaseModel subclasses."
            )

        setattr(cls, "__flock_model__", model)
        setattr(cls, "__flock_agent_description__", agent_description)

        # --- The Core Hydrate Method (Async) ---
        async def hydrate_method(self: T) -> T:
            """Hydrates the object by filling None fields using a dynamic Flock agent.
            Uses existing non-None fields as input context.
            Returns the hydrated object (self).
            """
            class_name = self.__class__.__name__
            logger.info(f"Starting hydration for instance of {class_name}")

            # 1. Introspect fields
            try:
                if hasattr(self, "model_fields"):  # Pydantic v2
                    all_fields = self.model_fields
                    type_hints = {
                        name: field.annotation
                        for name, field in all_fields.items()
                    }
                else:  # Pydantic v1 fallback
                    type_hints = get_type_hints(self.__class__)
                    all_fields = getattr(
                        self, "__fields__", {name: None for name in type_hints}
                    )
            except Exception as e:
                logger.error(
                    f"Could not get fields/type hints for {class_name}: {e}",
                    exc_info=True,
                )
                return self

            existing_data: dict[str, Any] = {}
            missing_fields: list[str] = []

            for field_name in all_fields.keys():
                if hasattr(self, field_name):  # Check if attribute exists
                    value = getattr(self, field_name)
                    if value is not None:
                        existing_data[field_name] = value
                    else:
                        missing_fields.append(field_name)
                # else: field defined in model but not set on instance yet - treat as missing
                #     missing_fields.append(field_name)

            if not missing_fields:
                logger.info(f"No fields to hydrate for {class_name} instance.")
                return self

            logger.debug(f"{class_name}: Fields to hydrate: {missing_fields}")
            logger.debug(
                f"{class_name}: Existing data for context: {json.dumps(existing_data, default=str)}"
            )

            # 2. Build dynamic Agent Signature Strings
            # Input signature based on existing data
            input_parts = []
            for name in existing_data:
                field_type = type_hints.get(name, Any)
                type_str = _format_type_to_string(field_type)  # Use helper
                # Get description from Pydantic Field if possible
                field_info = all_fields.get(name)
                field_desc = getattr(field_info, "description", "")
                if field_desc:
                    input_parts.append(f"{name}: {type_str} | {field_desc}")
                else:
                    input_parts.append(f"{name}: {type_str}")
            input_str = (
                ", ".join(input_parts)
                if input_parts
                else "context_info: dict | Optional context if no fields have values"
            )

            # Output signature based on missing fields (including nested types like 'Movie')
            output_parts = []
            for name in missing_fields:
                field_type = type_hints.get(name, Any)
                type_str = _format_type_to_string(field_type)  # Use helper
                field_info = all_fields.get(name)
                field_desc = getattr(field_info, "description", "")
                if field_desc:
                    output_parts.append(f"{name}: {type_str} | {field_desc}")
                else:
                    output_parts.append(f"{name}: {type_str}")
            output_str = ", ".join(output_parts)

            # 3. Create and Run Dynamic Agent
            agent_name = f"hydrator_{class_name}_{id(self)}"  # Make name unique per instance/call
            description = (
                getattr(self, "__flock_agent_description__", None)
                or f"Agent that completes missing data for a {class_name} object."
            )
            hydration_model = getattr(self, "__flock_model__", "openai/gpt-4o")

            logger.debug(
                f"Creating dynamic agent '{agent_name}' for {class_name}"
            )
            logger.debug(f"  Input Schema: {input_str}")
            logger.debug(
                f"  Output Schema: {output_str}"
            )  # e.g., "favorite_movie: Movie | The person's favorite movie"

            try:
                # Use the factory which likely sets up DeclarativeEvaluator by default
                dynamic_agent = FlockFactory.create_default_agent(
                    name=agent_name,
                    description=description,
                    input=input_str,
                    output=output_str,
                    model=hydration_model,
                    no_output=True,
                    use_cache=False,
                )

                temp_flock = Flock(
                    name=f"temp_hydrator_flock_{agent_name}",
                    model=hydration_model,
                    enable_logging=False,
                    show_flock_banner=False,
                )
                temp_flock.add_agent(dynamic_agent)

                agent_input_data = (
                    existing_data
                    if input_parts
                    else {"context_info": {"object_type": class_name}}
                )  # Pass type if no context

                logger.info(
                    f"Running hydration agent '{agent_name}' for {class_name}..."
                )

                result = await temp_flock.run_async(
                    start_agent=agent_name,
                    input=agent_input_data,
                    box_result=False,
                )
                logger.info(
                    f"Hydration agent returned for {class_name}: {list(result.keys())}"
                )

            except Exception as e:
                logger.error(
                    f"Hydration agent creation or run failed for {class_name}: {e}",
                    exc_info=True,
                )
                return self  # Return self without updates on failure

            # 4. Update self with results
            updated_count = 0
            for field_name in missing_fields:
                if field_name in result:
                    try:
                        # Set the attribute. Pydantic will validate/coerce if the type matches.
                        # If result[field_name] is a dict and field_name expects Movie,
                        # Pydantic should attempt instantiation.
                        setattr(self, field_name, result[field_name])
                        logger.debug(
                            f"Hydrated field '{field_name}' in {class_name} with value: {getattr(self, field_name)}"
                        )
                        updated_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to set hydrated value for '{field_name}' in {class_name}: {e}. Value received: {result[field_name]}"
                        )
                else:
                    logger.warning(
                        f"Hydration result missing expected field for {class_name}: '{field_name}'"
                    )

            logger.info(
                f"Hydration complete for {class_name}. Updated {updated_count}/{len(missing_fields)} fields."
            )
            return self

        # Attach the async method

        setattr(cls, "hydrate_async", hydrate_method)  # Alias

        # Add synchronous wrapper
        def sync_hydrate_wrapper(self: T) -> T:
            try:
                # Try to get the current running loop
                loop = asyncio.get_running_loop()

                # If we reach here, there is a running loop
                # We should use asyncio.run_coroutine_threadsafe instead
                if loop.is_running():
                    # This runs the coroutine in the existing loop from a different thread
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run, hydrate_method(self)
                        )
                        return future.result()
                else:
                    # There's a loop but it's not running
                    return loop.run_until_complete(hydrate_method(self))

            except RuntimeError:  # No running loop
                # If no loop is running, create a new one and run our coroutine
                return asyncio.run(hydrate_method(self))

        setattr(cls, "hydrate", sync_hydrate_wrapper)
        setattr(cls, "hydrate_sync", sync_hydrate_wrapper)

        logger.debug(f"Attached hydrate methods to class {cls.__name__}")
        return cls

    return decorator


# Ensure helper functions are available
# from flock.core.serialization.serialization_utils import _format_type_to_string
