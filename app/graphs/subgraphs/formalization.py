from typing import List
from functools import partial
import json
import re

from langchain_core.messages import HumanMessage
from langchain.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from app.graphs.prompts import FORMALIZATION_SYSTEM_PROMPT
from app.graphs.models import Plan
from app.graphs.state import PlanFormalizationState
from app.core.config import get_settings
from app.graphs.utils import is_plan_dag, refine_formalization_messages, format_agentkit_manifest

settings = get_settings()
model = ChatGoogleGenerativeAI(model=settings.gemini_model_name,
                              google_api_key=settings.gemini_api_key,
                              temperature=0)

def formalize_plan(state: PlanFormalizationState, tools: List[BaseTool]) -> PlanFormalizationState:
    agentkit_manifest = format_agentkit_manifest(tools)
    messages = refine_formalization_messages(state, 
                                             FORMALIZATION_SYSTEM_PROMPT.format(
                                                 plan_json_schema=Plan.model_json_schema(),
                                                 agentkit_manifest=agentkit_manifest
                                                 )
                                             )
    
    response = model.invoke(messages)
    
    split_pattern = r"\s*### PLAN ###\s*"
    parts = re.split(split_pattern, response.content, maxsplit=1)
    print(parts)

    if len(parts) == 2:
        reasoning_trace, plan_json = parts
    
    else:
        raise ValueError("No plan found in the content")
    
    plan_json = plan_json.strip().replace("```json", "").replace("```", "").strip("\n")
    
    plan = json.loads(plan_json)
    
    return {"plan": Plan.model_validate(plan)}

def validate_plan(state: PlanFormalizationState) -> Command:
    is_valid, error_message = is_plan_dag(state.get("plan"))
    if not is_valid:
        return Command(update={
            "error_log": [HumanMessage(content=error_message)],
                },
                       goto="formalize_plan")

    return Command(goto="feedback")

def feedback(state: PlanFormalizationState) -> PlanFormalizationState:
    user_feedback = interrupt({
        "steps": state["plan"].steps,
    })
    
    if user_feedback:
        return Command(update={
            "user_feedback": [HumanMessage(content=user_feedback)]},
                       goto="formalize_plan")
    
    return Command(goto=END)

def get_formalization_graph(tools: List[BaseTool]) -> StateGraph:
    workflow = StateGraph(PlanFormalizationState)
    
    workflow.add_node("formalize_plan", partial(formalize_plan, tools=tools))
    workflow.add_node("validate_plan", validate_plan)
    workflow.add_node("feedback", feedback)
    
    workflow.add_edge(START, "formalize_plan")
    workflow.add_edge("formalize_plan", "validate_plan")

    return workflow.compile()
    