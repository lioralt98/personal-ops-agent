from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.graphs.state import SupervisorState
from app.graphs.subgraphs.formalization import get_formalization_graph

checkpointer = InMemorySaver() 

def get_supervisor_graph() -> StateGraph:
    workflow = StateGraph(SupervisorState)
    
    workflow.add_node("formalization_graph", get_formalization_graph())
    
    workflow.add_edge(START, "formalization_graph")
    workflow.add_edge("formalization_graph", END)
    
    return workflow.compile(checkpointer=checkpointer)