from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from sqlmodel import Session
from langgraph.prebuilt import ToolNode
from langchain.tools import BaseTool
import json
from functools import partial

from app.core.config import get_settings
from app.tools.registry import load_tools
from app.models.user import UserPreferences
import app.services.users as users_service
from app.core.output import ChatInsights
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

settings = get_settings()

SYSTEM_PROMPT = """
                ### ROLE & OBJECTIVE
                You are the Personal Ops AI, a high-performance operational assistant designed to act as a technical Chief of Staff. Your goal is to maximize user efficiency by managing tasks, providing technical architectural advice, and facilitating workflows with precision.

                ### CORE OPERATING PRINCIPLES
                1. **Precision:** Provide direct, technically accurate answers. Minimize conversational filler.
                2. **Context Awareness:** Continuously reference the provided conversation summary to maintain continuity.
                3. **Preference Adherence:** Strictly follow the User Preferences defined in the JSON schema provided below. These override default behaviors.
                4. **Security:** Do not execute code or commands that could compromise the user's local environment unless explicitly authorized.
                5. **SCOPE ENFORCEMENT (CRITICAL):** You are NOT a general-purpose assistant. 
                   - Do NOT answer questions about general trivia, biology (e.g., "tell me about orcas"), pop culture, or news unless it directly relates to a specific task or project in the user's context.
                   - If a user asks an out-of-scope question, politely refuse: "I am designed to help with your operations and technical stack. I cannot assist with general topics."
                ### INSTRUCTIONS FOR DYNAMIC DATA
                You will be provided with two dynamic inputs appended to this instruction set:
                1. **Conversation Summary:** Use this to recall past decisions, project states, and user context.
                2. **User Preferences (JSON):** Treat this as your configuration file.
                  - If `communication_style` is defined, mimic it exactly.
                  - If `tech_stack` is defined, prioritize those tools in recommendations.
                  - If `constraints` are listed, treat them as hard blockers.

                ### FORMATTING STANDARDS
                - **Code:** Always use markdown blocks with language identifiers.
                - **Complex Logic:** Use step-by-step reasoning (Chain of Thought) for architectural or debugging queries.
                - **Brevity:** If the user asks a yes/no question, provide a yes/no answer followed by a single sentence of context if necessary.

                ---
                ### END OF SYSTEM INSTRUCTIONS. DYNAMIC CONTEXT FOLLOWS:
"""

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
                              google_api_key=settings.gemini_api_key,
                              temperature=0)

extract_preferences_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that maintains user profiles. 
    Analyze the conversation history below. 
    
    Current User Preferences:
    {current_prefs}
    
    Extract any NEW preferences mentioned. If none, return empty fields.
    """),
    MessagesPlaceholder(variable_name="messages") 
])

preferences_extractor = extract_preferences_prompt | model.with_structured_output(ChatInsights)

checkpointer = InMemorySaver()

class State(MessagesState):
  summary: str
  user_id: int
  user_preferences: UserPreferences
  
def load_data(state: State, config: RunnableConfig) -> State:
  if not state.get("user_preferences"):
    user_preferences = users_service.get_user_preferences(state.get("user_id"), config["configurable"]["session"])
    return {"user_preferences": user_preferences}
  return {}

def summarize_conversation(state: State) -> State:
  summary = state.get("summary", "")
  
  if summary:
    summary_message = f"Summary of earlier conversation: {summary}\n\nExtend the summary with the messages above."
  
  else:
    summary_message = "Summarize the conversation above."
  
  messages = state.get("messages") + [HumanMessage(content=summary_message)]
  result = model.invoke(messages)
  
  trim_messages = [RemoveMessage(id=m.id) for m in messages[:-2]]
  return {"summary": result.content, "messages": trim_messages}

def update_user_preferences(state: State, config: RunnableConfig) -> State:
  current_prefs = state.get("user_preferences")
  session = config["configurable"]["session"]
  current_prefs_json = current_prefs.model_dump_json(exclude_none=True,
                                                     exclude={"id", "user_id"})
  
  # Gemini requires the chat history to end with a HumanMessage
  messages = state.get("messages")[-2:]
  analyze_messages = messages + [HumanMessage(content="Extract preferences from the conversation above.")]
  
  extracted_prefs = preferences_extractor.invoke({"current_prefs": current_prefs_json,
                                                  "messages": analyze_messages})

  # if updates_for_prefs:
  users_service.update_user_preferences(current_prefs.id, extracted_prefs, session)
  return {"user_preferences": users_service.get_user_preferences(state.get("user_id"), session)}

def post_conversation_router(state: State) -> List[str]:
  if state.get("messages")[-1].tool_calls:
    return "tools"
  
  dest = ["update_user_preferences"]
  num_messages = len(state.get("messages"))
  
  if num_messages > 5:
    dest.append("summarize_conversation")
  
  return dest

def call_llm(state: State, model_with_tools: Runnable) -> State:
    summary = state.get("summary")
    user_preferences = state.get("user_preferences", None)
    
    system_prompt = SYSTEM_PROMPT
    
    if summary:
      system_prompt += f"Summary of earlier conversation: {summary}"
      
    if user_preferences:
      user_preferences_dict = user_preferences.model_dump(exclude_none=True,
                                                          exclude={"id", "user_id"})
      if user_preferences_dict:
        system_prompt += f"User preferences: {json.dumps(user_preferences_dict)}"
    
    if system_prompt:
      messages = [SystemMessage(content=system_prompt)] + state.get("messages") 
    
    else:
      messages = state.get("messages")
    
    result = model_with_tools.invoke(messages)
    print(f"RESULT: {result}")
    return {"messages": result}

def get_agent(user_scopes: set[str], user_domains: set[str]):
  tools = load_tools(user_scopes, user_domains)
  model_with_tools = model.bind_tools(tools)
  call_llm_node = partial(call_llm, model_with_tools=model_with_tools)

  workflow = StateGraph(State)
  workflow.add_node("load_data", load_data)
  workflow.add_node("conversation", call_llm_node)
  workflow.add_node("tools", ToolNode(tools))
  workflow.add_node("summarize_conversation", summarize_conversation)
  workflow.add_node("update_user_preferences", update_user_preferences)

  workflow.add_edge(START, "load_data")
  workflow.add_edge("load_data", "conversation")
  workflow.add_conditional_edges("conversation", post_conversation_router)
  workflow.add_edge("tools", "conversation")
  workflow.add_edge("update_user_preferences", END)
  workflow.add_edge("summarize_conversation", END)

  agent = workflow.compile(checkpointer=checkpointer)
  
  return agent