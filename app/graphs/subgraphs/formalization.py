from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

from app.graphs.models import Plan
from app.graphs.state import PlanFormalizationState
from app.core.config import get_settings
from app.graphs.utils import is_plan_dag

settings = get_settings()
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
                              google_api_key=settings.gemini_api_key,
                              temperature=0)

FORMALIZATION_SYSTEM_PROMPT = """
You are an expert Strategic Planner Agent. Your goal is to map out a concrete execution path to achieve the user's objective.

You operate in a "Human-in-the-Loop" workflow. You will receive a history of feedback messages from a human supervisor. Your job is to generate or refine a `Plan` (a list of `Task` objects) based on the LATEST feedback while maintaining the progress of agreed-upon parts of the plan.

### YOUR DATA STRUCTURE
You must output a structured `Plan` object containing a list of `Task`s. Follow these strict field definitions:

1. **task_id**: A unique, concise string identifier (e.g., "1", "2", "search_1", "review_3").
2. **title**: An action-oriented description starting with a verb (e.g., "Scrape competitor prices", "Review draft").
3. **reasoning**: A clear justification. Why is this task necessary? How does it address the user's specific feedback?
4. **task_dest**:
   - "agent": Use this for ANY task involving creation, preparation, analysis, coding, scheduling, or data fetching. The Agent does the "heavy lifting" and preparation.
   - "user": Use this ONLY for the final performance, physical action, or private authentication. The User typically *consumes* or *acts upon* what the Agent has prepared.
5. **dependencies**: A list of `task_id`s that must complete *before* this task can start.

### PLANNING LOGIC & RULES
1. **Logical Flow**: Ensure the `dependencies` create a valid Directed Acyclic Graph (DAG). Task B cannot depend on Task A if Task A depends on Task B. No infinite loops.
2. **Granularity**: Break complex goals into atomic, manageable steps. A task should represent a single specific outcome.
3. **Agent Capability & Tooling**: 
   - Never assign "scheduling", "emailing", or "data fetching" to the user. The agent has tools for this. 
4. **Handling Credentials**: 
   - Distinguish between *providing* access (User) and *using* access (Agent). 
   - If an API Key is needed, create a User task: "Provide API Key," then an Agent task: "Fetch data using API Key."
5. **Separation of Creation & Usage (The 'Prep-then-Act' Rule)**:
   - **CRITICAL**: Never assign a broad task to the User if the Agent can prepare the materials first.
   - **Pattern**: Split tasks into `Agent: Create/Setup` -> `User: Perform/Use`.
   - *Example*: Instead of "User: Conduct Mock Interview", generate "Agent: Generate Interview Script" -> "User: Perform Interview using Script".
   - *Example*: Instead of "User: Study Biology", generate "Agent: Create Biology Flashcards" -> "User: Review Flashcards".
6. **Sequential vs. Parallel**: If tasks don't rely on each other's output, do not link them as dependencies. Allow them to run in parallel to save time.

### BEHAVIOR ON ITERATION
The user input will be a conversation history. You must:
1. Analyze the *entire* history to understand the context.
2. Prioritize the *last* message as the current constraint or correction.
3. Return the FULL plan every time. Do not return just the changes; return the complete list of tasks representing the current state of the plan.

Think step-by-step about the dependencies before generating the final structure.
"""

def formalize_plan(state: PlanFormalizationState) -> PlanFormalizationState:
    formalization_system_message = SystemMessage(content=FORMALIZATION_SYSTEM_PROMPT)
    model_with_structured_output = model.with_structured_output(Plan)
    print(state.get("human_feedback"))
    result = model_with_structured_output.invoke([formalization_system_message] + state.get("human_feedback"))
    
    return {"plan": result}

def validation_plan(state: PlanFormalizationState) -> Literal["validate_plan", "formalize_plan"]:
    is_valid, message = is_plan_dag(state.get("plan"))
    if not is_valid:
        return Command(update={
            "human_feedback": [HumanMessage(content=f"The plan is invalid. {message}. Please fix the plan and try again.")],
                },
                       goto="formalize_plan")

    return Command(goto="feedback")

def feedback(state: PlanFormalizationState) -> PlanFormalizationState:
    user_feedback = interrupt({
        "plan": state.get("plan"),
    })
    
    if user_feedback:
        return Command(update={"human_feedback": [HumanMessage(content=user_feedback)]},
                       goto="formalize_plan")
    
    return Command(goto=END)

def get_formalization_graph() -> StateGraph:
    workflow = StateGraph(PlanFormalizationState)
    
    workflow.add_node("formalize_plan", formalize_plan)
    workflow.add_node("validation_plan", validation_plan)
    workflow.add_node("feedback", feedback)
    
    workflow.add_edge(START, "formalize_plan")
    workflow.add_edge("formalize_plan", "validation_plan")

    return workflow.compile()
    