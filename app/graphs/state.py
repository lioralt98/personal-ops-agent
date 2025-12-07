from typing import TypedDict, Annotated, List

import operator
from langgraph.graph import add_messages
from langchain_core.messages import HumanMessage

from app.graphs.models import Plan, SearchQuery

class PlanFormalizationState(TypedDict):
    plan: Plan
    goal: str
    user_feedback: Annotated[List[HumanMessage], add_messages]
    error_log: Annotated[List[HumanMessage], add_messages]

class SupervisorState(TypedDict):
    user_id: int
    goal: str
    plan: Plan
    output_context: str
    search_queries: List[SearchQuery]
    sections: Annotated[List[str], operator.add]

class ContextState(TypedDict):
    goal: str
    search_queries: List[SearchQuery]
    output_context: str
    sections: Annotated[List[str], operator.add]

class OpsState(TypedDict):
    pass
    