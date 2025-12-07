from typing import Literal, List, Tuple
from datetime import datetime, timezone
from functools import partial

from langchain_core.messages import SystemMessage
from langchain.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

from app.graphs.prompts import OPS_SYSTEM_PROMPT
from app.graphs.state import OpsState
from app.core.config import get_settings

settings = get_settings()

model = ChatGoogleGenerativeAI(model=settings.gemini_model_name,
                              google_api_key=settings.gemini_api_key,
                              temperature=0)

def tool_router(state: OpsState) -> Literal["tools", END]:
    if state.get("messages")[-1].tool_calls:
        return "tools"
    return END

def call_llm(state: OpsState, tools: List[BaseTool]) -> OpsState:
    model_with_tools = model.bind_tools(tools)
    formated_system_prompt = OPS_SYSTEM_PROMPT.format(current_time_utc=datetime.now(timezone.utc).isoformat(),
                                             user_timezone=state.get("user_preferences").timezone)
    messages = [SystemMessage(content=formated_system_prompt)] + state.get("messages")
    result = model_with_tools.invoke(messages)
    return {"messages": result}

def get_ops_graph(tools: List[BaseTool]) -> StateGraph:
    call_llm_node = partial(call_llm, tools=tools)
    workflow = StateGraph(OpsState)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("call_llm", call_llm_node)
    
    workflow.add_edge(START, "call_llm")
    workflow.add_edge("tools", "call_llm")
    workflow.add_conditional_edges("call_llm", tool_router)
    return workflow.compile()