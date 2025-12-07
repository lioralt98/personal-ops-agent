from typing import List

from langchain.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.graphs.state import SupervisorState
from app.graphs.subgraphs.formalization import get_formalization_graph
from app.graphs.subgraphs.context import get_context_graph
from app.graphs.subgraphs.ops import get_ops_graph
from app.tools.registry import load_tools

checkpointer = InMemorySaver()

def get_supervisor_graph(user_scopes: set[str], user_domains: set[str]) -> StateGraph:
    tools = load_tools(user_scopes, user_domains)
    workflow = StateGraph(SupervisorState)
    
    workflow.add_node("ops_graph", get_ops_graph(tools))
    workflow.add_node("formalization_graph", get_formalization_graph(tools))
    workflow.add_node("context_graph", get_context_graph())
    
    workflow.add_edge(START, "formalization_graph")
    workflow.add_edge("formalization_graph", END)
    
    return workflow.compile(checkpointer=checkpointer)