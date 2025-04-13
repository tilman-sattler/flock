# 🚀 Flock: The Declarative AI Agent Framework 🚀

<p align="center">
  <!-- Placeholder for your Flock Logo/Banner - Replace URL -->
  <img alt="Flock Banner" src="https://raw.githubusercontent.com/whiteducksoftware/flock/master/docs/assets/images/flock.png" width="600">
</p>
<p align="center">
  <!-- Update badges -->
  <a href="https://pypi.org/project/flock-core/" target="_blank"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/flock-core?style=for-the-badge&logo=pypi&label=pip%20version"></a>
  <img alt="Python Version" src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python">
  <a href="https://github.com/whiteducksoftware/flock/actions/workflows/deploy-whiteduck-pypi.yml" target="_blank"><img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/whiteducksoftware/flock/deploy-whiteduck-pypi.yml?branch=master&style=for-the-badge&logo=githubactions&logoColor=white"></a>
  <a href="https://github.com/whiteducksoftware/flock/blob/master/LICENSE" target="_blank"><img alt="License" src="https://img.shields.io/pypi/l/flock-core?style=for-the-badge"></a>
  <a href="https://whiteduck.de" target="_blank"><img alt="Built by white duck" src="https://img.shields.io/badge/Built%20by-white%20duck%20GmbH-white?style=for-the-badge&labelColor=black"></a>
  <a href="https://www.linkedin.com/company/whiteduck" target="_blank"><img alt="LinkedIn" src="https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white&label=whiteduck"></a>
<a href="https://bsky.app/profile/whiteduck-gmbh.bsky.social" target="_blank"><img alt="Bluesky" src="https://img.shields.io/badge/bluesky-Follow-blue?style=for-the-badge&logo=bluesky&logoColor=%23fff&color=%23333&labelColor=%230285FF&label=whiteduck-gmbh"></a>
</p>

🐤 Flock 0.4.0 currently in beta - use `pip install flock-core==0.4.0b5` 🐤

🐤 `pip install flock-core` will install the latest non-beta version 🐤

🐤  Expected Release for 0.4.0 `Magpie`: End of April 2025 🐤

---

**Tired of wrestling with paragraphs of prompt text just to get your AI agent to perform a specific, structured task?** 😫

Enter **Flock**, the agent framework that lets you ditch the prompt-palaver and focus on **what** you want your agents to achieve through a **declarative approach**. Define your agent's inputs, outputs, and available tools using clear Python structures (including type hints!), and let Flock handle the complex LLM interactions and orchestration.

Built with real-world deployment in mind, Flock integrates seamlessly with tools like **Temporal** (optional) for building robust, fault-tolerant, and scalable agent systems right out of the box.

**Looking for examples and tutorials?** Check out the dedicated [**👉 flock-showcase Repository**](https://github.com/whiteducksoftware/flock-showcase)!

## ✨ Why Join the Flock?

Flock offers a different way to build agentic systems:

| Traditional Agent Frameworks 😟        | Flock Framework 🐤🐧🐓🦆             |
| :------------------------------------- | :------------------------------------ |
| 🤯 **Prompt Nightmare**                | ✅ **Declarative Simplicity**         |
| *Long, brittle, hard-to-tune prompts*  | *Clear input/output specs (typed!)*   |
| 💥 **Fragile & Unpredictable**         | ⚡ **Robust & Production-Ready**     |
| *Single errors can halt everything*    | *Fault-tolerant via Temporal option*  |
| 🧩 **Monolithic & Rigid**             | 🔧 **Modular & Flexible**             |
| *Hard to extend or modify logic*       | *Pluggable Evaluators, Modules, Tools*|
| ⛓️ **Basic Chaining**                 | 🚀 **Advanced Orchestration**         |
| *Often just linear workflows*          | *Dynamic Routing, Batch Processing*   |
| 🧪 **Difficult Testing**               | ✅ **Testable Components**            |
| *Hard to unit test prompt logic*       | *Clear I/O contracts aid testing*     |
| 📄 **Unstructured Output**             | ✨ **Structured Data Handling**       |
| *Parsing unreliable LLM text output*   | *Native Pydantic/Typed Dict support*  |

## 💡 Core Concepts

Flock's power comes from a few key ideas (Learn more in the [Full Documentation](https://whiteducksoftware.github.io/flock/)):

1. **Declarative Agents:** Define agents by *what* they do (inputs/outputs), not *how*. Flock uses **Evaluators** (like the default `DeclarativeEvaluator` powered by DSPy) to handle the underlying logic.
2. **Typed Signatures:** Specify agent inputs and outputs using Python type hints and optional descriptions (e.g., `"query: str | User request, context: Optional[List[MyType]]"`).
3. **Modular Components:** Extend agent capabilities with pluggable **Modules** (e.g., for memory, metrics, output formatting) that hook into the agent's lifecycle.
4. **Intelligent Workflows:** Chain agents explicitly or use **Routers** (LLM-based, Agent-based, or custom) for dynamic decision-making.
5. **Reliable Execution:** Run locally for easy debugging or seamlessly switch to **Temporal** (optional) for production-grade fault tolerance, retries, and state management.
6. **Tool Integration:** Equip agents with standard or custom Python functions (`@flock_tool`) registered via the `FlockRegistry`.
7. **Registry:** A central place (`@flock_component`, `@flock_type`, `@flock_tool`) to register your custom classes, types, and functions, enabling robust serialization and dynamic loading.

## 💾 Installation

Get started with the core Flock library:

```bash
# Using uv (recommended)
uv pip install flock-core

# Using pip
pip install flock-core
```

Extras: Install optional dependencies for specific features:

```bash
# Common tools (Tavily, Markdownify)
uv pip install flock-core[tools]

# All optional dependencies (including tools, docling, etc.)
uv pip install flock-core[all]
```

Environment Setup:

Flock uses environment variables (typically in a .env file) for configuration, especially API keys. Create a .env file in your project root:

```bash
# .env - Example

# --- LLM Provider API Keys (Required by most examples) ---
# Add keys for providers you use (OpenAI, Anthropic, Gemini, Azure, etc.)
# Refer to litellm docs (https://docs.litellm.ai/docs/providers) for names
OPENAI_API_KEY="your-openai-api-key"
# ANTHROPIC_API_KEY="your-anthropic-api-key"

# --- Tool-Specific Keys (Optional) ---
# TAVILY_API_KEY="your-tavily-search-key"
# GITHUB_PAT="your-github-personal-access-token"

# --- Default Flock Settings (Optional) ---
DEFAULT_MODEL="openai/gpt-4o" # Default LLM if agent doesn't specify

# --- Flock CLI Settings (Managed by `flock settings`) ---
# SHOW_SECRETS="False"
# VARS_PER_PAGE="20"
```

Remember to add .env to your .gitignore!

## ⚡ Quick Start Syntax

While detailed examples and tutorials now live in the flock-showcase repository, here's a minimal example to illustrate the core syntax:

```python
from flock.core import Flock, FlockFactory

# 1. Create the main orchestrator
# Uses DEFAULT_MODEL from .env or defaults to "openai/gpt-4o" if not set
my_flock = Flock(name="SimpleFlock")

# 2. Declaratively define an agent using the Factory
# Input: a topic (string)
# Output: a title (string) and bullet points (list of strings)
brainstorm_agent = FlockFactory.create_default_agent(
    name="idea_generator",
    description="Generates titles and key points for a given topic.",
    input="topic: str | The subject to brainstorm about",
    output="catchy_title: str, key_points: list[str] | 3-5 main bullet points"
)

# 3. Add the agent to the Flock
my_flock.add_agent(brainstorm_agent)

# 4. Run the agent!
if __name__ == "__main__":
    input_data = {"topic": "The future of AI agents"}
    try:
        # The result is a Box object (dot-accessible dict)
        result = my_flock.run(start_agent="idea_generator", input=input_data)
        print(f"Generated Title: {result.catchy_title}")
        print("Key Points:")
        for point in result.key_points:
            print(f"- {point}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Ensure your LLM API key (e.g., OPENAI_API_KEY) is set in your .env file!")
```

## ✨ Utility: @flockclass Hydrator

Flock also provides conveniences. The @flockclass decorator allows you to easily populate Pydantic models using an LLM:

```python
from pydantic import BaseModel
from flock.util.hydrator import flockclass # Assuming hydrator utility exists
import asyncio

@flockclass(model="openai/gpt-4o") # Decorate your Pydantic model
class CharacterIdea(BaseModel):
    name: str
    char_class: str
    race: str
    backstory_hook: str | None = None # Field to be filled by hydrate
    personality_trait: str | None = None # Field to be filled by hydrate

async def create_character():
    # Create with minimal data
    char = CharacterIdea(name="Gorok", char_class="Barbarian", race="Orc")
    print(f"Before Hydration: {char}")

    # Call hydrate to fill in the None fields using the LLM
    hydrated_char = await char.hydrate()

    print(f"\nAfter Hydration: {hydrated_char}")
    print(f"Backstory Hook: {hydrated_char.backstory_hook}")

# asyncio.run(create_character())
```

## 📚 Examples & Tutorials

For a comprehensive set of examples, ranging from basic usage to complex projects and advanced features, please visit our dedicated showcase repository:

➡️ [github.com/whiteducksoftware/flock-showcase](https://github.com/whiteducksoftware/flock-showcase) ⬅️

The showcase includes:

- Step-by-step guides for core concepts.
- Examples of tool usage, routing, memory, and more.
- Complete mini-projects demonstrating practical applications.

## 📖 Documentation

Full documentation, including API references and conceptual explanations, can be found at:

➡️ [whiteducksoftware.github.io/flock/](https://whiteducksoftware.github.io/flock/) ⬅️

## 🤝 Contributing

We welcome contributions! Please see the CONTRIBUTING.md file (if available) or open an issue/pull request on GitHub.

Ways to contribute:

- Report bugs or suggest features.
- Improve documentation.
- Contribute new Modules, Evaluators, or Routers.
- Add examples to the flock-showcase repository.
- Join our Discord Community to discuss development! <!-- Add Discord link -->

## 📜 License

Flock is licensed under the Apache License 2.0. See the LICENSE file for details.

## 🏢 About

Flock is developed and maintained by white duck GmbH, your partner for cloud-native solutions and AI integration.
