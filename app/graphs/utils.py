from collections import defaultdict, deque
from typing import Tuple, List

from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.utils.function_calling import convert_to_openai_function

from app.graphs.prompts import FEEDBACK_PROMPT, ERROR_PROMPT
from app.graphs.models import Plan
from app.graphs.state import PlanFormalizationState

def refine_formalization_messages(state: PlanFormalizationState, system_prompt: str) -> List[BaseMessage]:
    messages = [SystemMessage(content=system_prompt)]
    
    if state.get("goal"):
        messages.append(HumanMessage(content=f" Origin user goal: {state.get("goal")}"))
        
    if state.get("plan"):
        messages.append(HumanMessage(content=f" Origin plan: {state.get("plan").model_dump_json()}"))
    
    for message in state.get("user_feedback"):
        structured_message = FEEDBACK_PROMPT.format(user_feedback=message.content)
        messages.append(HumanMessage(content=structured_message))
    
    for error in state.get("error_log"):
        structured_error = ERROR_PROMPT.format(error=error.content)
        messages.append(HumanMessage(content=structured_error))
    
    return messages

def format_agentkit_manifest(tools: List[BaseTool]) -> str:
    manifest = "### OPS AGENT:\ndescription: The Ops Agent is responsible for executing operational tasks via external APIs (Google Calendar, Google Tasks).\ncapabilities:\n"
    
    for tool in tools:
        func_desc = convert_to_openai_function(tool)
        name = func_desc["name"]
        args = ", ".join(func_desc["parameters"]["properties"].keys())
        
        manifest += f"- {name} ({args}): {func_desc["description"][:100]}...\n"
    
    manifest += "---\n"
    manifest += """### CONTEXT AGENT:
    description: The Context Agent is responsible for gathering summerized information from the internet.
    capabilities:
    - web search"""
    
    return manifest
        
def is_plan_dag(plan: Plan) -> Tuple[bool, str]:
    adj = defaultdict(list)
    step_ids = set([step.id for step in plan.steps])
    in_degree = defaultdict(int)
    
    for step in plan.steps:
        dep_set = set(step.dependencies)
        if len(dep_set) != len(step.dependencies):
            return False, f"Error: Dependencies IDs in step {step.id} are not unique."
        if not dep_set.issubset(step_ids):
            return False, f"Error: One or more dependencies IDs from step {step.id} are not found in steps."

        for dep in dep_set:
            adj[dep].append(step.id)
            in_degree[step.id] += 1
    
    q = deque([step_id for step_id in adj.keys() if in_degree[step_id] == 0])
    visited_steps = 0
    
    while q:
        cur_step_id = q.popleft()
        visited_steps += 1
        
        for nei in adj[cur_step_id]:
            in_degree[nei] -= 1
            if in_degree[nei] == 0:
                q.append(nei)
    
    if visited_steps < len(adj):
        return False, "Error: The plan contains a cycle."
    return True, "Success: The plan is a DAG."