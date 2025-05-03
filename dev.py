from typing import Any, Callable
from flock.core.context.context import FlockContext
from flock.core.flock_agent import FlockAgent
from flock.core.flock_router import HandOffRequest
from flock.core.logging.formatters.themes import OutputTheme
from flock.evaluators.declarative.declarative_evaluator import DeclarativeEvaluator, DeclarativeEvaluatorConfig
from flock.modules.output.output_module import OutputModule, OutputModuleConfig
from flock.modules.performance.metrics_module import MetricsModule, MetricsModuleConfig
from flock.routers.default.default_router import DefaultRouter, DefaultRouterConfig
from flock.routers.llm.llm_router import LLMRouter, LLMRouterConfig


def dev():
  print("DEVELOPMENT!!! DO NOT COMMIT!!!")
  
  from flock.core import Flock
  
  llm_router_config = LLMRouterConfig(
    enabled=True,
    agents=[
      "presentation_finalization_agent",
      "iterative_enhancement_agent",
      "presentation_checking_agent",
    ]
  )
  
  llm_router = LLMRouter(
    name="llm_router",
    config=llm_router_config
  )
  
  model = "azure/gpt-4o"
  
  eval_config = DeclarativeEvaluatorConfig(
    model=model,
    use_cache=True,
    max_tokens=4096,
    temperature=0.0,
    stream=False,
    include_thought_process=False
  )
  
  evaluator = DeclarativeEvaluator(
    name="default",
    config=eval_config
  )
  
  output_module_config = OutputModuleConfig(
    render_table=True,
    theme=OutputTheme.apple_system_colors,
    no_output=False,
    print_context=False,
  )
  
  output_module = OutputModule("output", config=output_module_config)
  
  
  metrics_config = MetricsModuleConfig(
    latency_threshold_ms=3000
  )
  metrics_module = MetricsModule("metrics", config=metrics_config)
  
  presentation_agent_input = """
    topic: str | the topic the presentation is about,
    remarks: str | (optional) additional instructions or remarks for the creation of the presentation,
    type: str | the type of the presentation,
    target_audience: str | the target audience of the presentation,
    subtopics: list[str] | (optional) subtopics to cover initially,
    preferred_number_of_slides: int | the preferred number of slides for the presentation (relevant for number of subtopics),
    suggest_additional_subtopics: bool | whether or not to suggest additional subtopics for the presentation,
    """
  presentation_agent_output = """
    title: str | the title of the presentation,
    subtitle: str | subtitle for the presentation,
    type: str | the type of the presentation,
    target_audience: str | the target audience of the presentation,
    subtopics: list[str] | a list of subtopics to cover (including suggested subtopics),
    """
    
  checking_agent_output = """
    check_passed: bool | 'True' if the outline of the presentation passed the check 'False' otherwise,
    suggestions: list[str] | (optional) a list of suggestions for correcting or enhancing the outline,
    additional_subtopics: list[str] | (optional) subtopics which should be covered as well,
    subtopics_to_remove: list[str] | (optional) subtopics which can be removed from the outline,
    target_audience: str | the target audience of the presentation,
    """
  
  correction_agent_output = """
  title: str | the title of the presentation,
  subtitle: str | the subtitle of the presentation,
  type: str | the type of the presentation,
  target_audience: str | the target audience of the presentation,
  subtopics: list[str] | a list of subtopics to cover in the presentation,
  """
  
  finalization_agent_output="""
  title: str | the title of the presentation,
  subtitle: str | the subtitle of the presentation,
  target_audience: str | the target audience of the presentation,
  slide_headers: list[str] | a list of headers for the slides of the presentation,
  topics_covered: list[str] | a list of topics covered in the presentation,
  """
  
  finalization_agent = FlockAgent(
    name="presentation_finalization_agent",
    description="Creates a final presentation outline for a given topic with titles a list of topics to cover and headers for each slide in the presentation",
    input=correction_agent_output,
    output=finalization_agent_output,
    model=model,
    evaluator=evaluator,
    modules=
      {
        output_module.name : output_module,
        metrics_module.name : metrics_module,
      }
  )
  
  correction_agent = FlockAgent(
    name="iterative_enhancement_agent",
    description="Enhances and corrects a presentation outline based on the provided suggestions",
    input=f"""
    {presentation_agent_output}
    {checking_agent_output}
    """,
    output=correction_agent_output,
    model=model,
    evaluator=evaluator,
    modules={
      output_module.name : output_module,
      metrics_module.name : metrics_module,
    },
    handoff_router=llm_router
  )
    
  checking_agent = FlockAgent(
    name="presentation_checking_agent",
    description="Double-Checks a presentation outline for potentially missing items and factual errors and provides suggestions for enhancements",
    input=presentation_agent_output,
    output=checking_agent_output,
    model=model,
    evaluator=evaluator,
    modules={
      output_module.name : output_module,
      metrics_module.name : metrics_module,
    },
    handoff_router=llm_router
  )
  
  
  presentation_agent = FlockAgent(
    name="presentation_suggestion_agent",
    description="Suggests a possible outline for a presentation on the provided topic",
    input=presentation_agent_input,
    output=presentation_agent_output,
    model=model,
    evaluator=evaluator,
    modules={
      output_module.name : output_module,
      metrics_module.name : metrics_module,
    },
    handoff_router=llm_router
  )
  

  
  
  
  flock = Flock(
    name = "presentation_helper",
    description="Helps build detailed presentations",
    model=model,
    enable_logging=True,
    agents=[
      presentation_agent,
      checking_agent,
      correction_agent,
      finalization_agent,
      ]
  )
  
  input_dict = {
    "topic": "An Introduction to Deep Learning, Chapter 1",
    "remarks": "The presentation should cover the basics but should not shy away from explaining mathematical core concepts. Keep the title intact.",
    "type": "university lecture",
    "target_audience": "University Students doing their Master's degree in Computer Science",
    "subtopics": [
      "Perceptrons",
      "Multi-Layer-Perceptrons",
      "Gradient Descent",
      "Learing-Rate",
      "Hyperparameters",
      "Regression",
      "Classification",
    ],
    "preferred_number_of_slides": 60,
    "suggest_additional_subtopics": True,
  }
  
  result = flock.run(
    start_agent=presentation_agent,
    input=input_dict,
  )
  
  print(f"\n######## OUTPUT: ########")
  print(f"# TITLE:           {result.title}")
  print(f"# SUBTITLE:        {result.subtitle}")
  print(f"# TYPE:            {result.type}")
  print(f"# TARGET AUDIENCE: {result.target_audience}")
  print(f"# SLIDE HEADERS:")
  for header in result.slide_headers:
    print(f"  - {header}")
  print(f"# TOPICS COVERED:")
  for topic in result.topics_covered:
    print(f"  - {topic}")
    
  


  
if __name__ == "__main__":
  dev()