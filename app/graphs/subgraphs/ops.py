from typing import Literal, List
from functools import partial

from langchain_core.messages import SystemMessage
from langchain.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

from app.graphs.state import State
from app.core.config import get_settings

settings = get_settings()

OPS_SYSTEM_PROMPT = """
### ROLE & OBJECTIVE
You are the **OpsExecutionUnit**, a specialized sub-agent responsible for the precise execution of operational tasks via external APIs (Google Calendar, Google Tasks). 
Your sole function is to translate user intents into valid, executable tool calls. You do not engage in casual conversation, advice, or strategic planning.

### OPERATIONAL CONSTRAINTS
1. **Silent Execution:** Do not provide conversational filler (e.g., "I will do that now," "Sure thing"). Immediately generate the required tool call.
2. **Parameter Strictness:** - Ensure all date-time strings conform strictly to **ISO 8601** (e.g., `YYYY-MM-DDTHH:MM:SS`).
   - For Google Tasks, default to `tasklist_id='@default'` unless a specific list ID is provided in the context.
   - For Google Calendar, ensure `start` and `end` times are logically consistent (start < end).
3. **Ambiguity Handling:** - If a required parameter (e.g., 'title', 'date') is missing and cannot be inferred from the context, do NOT guess. 
   - Return a final response stating EXACTLY which parameter is missing so the supervisor can prompt the user.
4. **Error Recovery:** If a tool execution fails (e.g., invalid ID), analyze the error message provided by the tool output and attempt a correction ONLY if it is a formatting error. Otherwise, report the failure.

### INPUT DATA
You operate on a state containing:
- `messages`: The conversation history focused on the specific request.
- `user_preferences`: User configuration (e.g., `timezone`) which MUST be applied to all date/time calculations.

### OUTPUT FORMAT
- **Primary:** A `tool_call` object matching the schema of the requested operation.
- **Secondary (Post-Execution):** A terse, factual confirmation string (e.g., "Task 'Buy Milk' created in list '@default' with ID 12345.") or a structured error report.

### DATE/TIME CONTEXT
- Current Time (UTC): {current_time_utc}
- User Timezone: {user_timezone}
"""

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
                              google_api_key=settings.gemini_api_key,
                              temperature=0)

def tool_router(state: State) -> Literal["tools", END]:
    if state.get("messages")[-1].tool_calls:
        return "tools"
    return END

def call_llm(state: State, tools: List[BaseTool]) -> State:
    model_with_tools = model.bind_tools(tools)
    formated_system_prompt = OPS_SYSTEM_PROMPT.format(current_time_utc=datetime.now(timezone.utc).isoformat(),
                                             user_timezone=state.get("user_preferences").timezone)
    messages = [SystemMessage(content=formated_system_prompt)] + state.get("messages")
    result = model_with_tools.invoke(messages)
    return {"messages": result}

def get_ops_graph(tools: List[BaseTool]) -> StateGraph:
    call_llm_node = partial(call_llm, tools=tools)
    workflow = StateGraph(State)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("call_llm", call_llm_node)
    
    workflow.add_edge(START, "call_llm")
    workflow.add_edge("tools", "call_llm")
    workflow.add_conditional_edges("call_llm", tool_router)
    return workflow.compile()