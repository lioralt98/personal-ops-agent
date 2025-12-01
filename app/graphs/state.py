from typing import TypedDict, Annotated, List
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

from app.graphs.models import Plan

class PlanFormalizationState(TypedDict):
    plan: Plan
    human_feedback: Annotated[List[BaseMessage], add_messages]

class SupervisorState(TypedDict):
    human_feedback: Annotated[List[BaseMessage], add_messages]
    user_id: int
    plan: Plan