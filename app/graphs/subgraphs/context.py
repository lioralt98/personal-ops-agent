from typing import List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_tavily import TavilySearch

from app.graphs.prompts import (
    QUERIES_SYSTEM_PROMPT,
    SECTION_WRITING_SYSTEM_PROMPT,
    FINAL_CONTEXT_SYSTEM_PROMPT
    )
from app.graphs.state import ContextState
from app.core.config import get_settings
from app.graphs.models import SearchQueryList

settings = get_settings()
model = ChatGoogleGenerativeAI(model=settings.gemini_model_name,
                              google_api_key=settings.gemini_api_key,
                              temperature=0)
tavily_search = TavilySearch(max_results=3,
                            include_raw_content=True,
                            include_favicon=False,
                             tavily_api_key=settings.tavily_api_key)

def generate_search_queries(state: ContextState) -> ContextState:
    system_message = SystemMessage(content=QUERIES_SYSTEM_PROMPT.format(
        goal=state.get("goal"),
        NUM_QUERIES=3
    ))
    human_message = HumanMessage(content=f"User's goal: {state.get("goal")}")
    model_with_structured_output = model.with_structured_output(SearchQueryList)
    
    queries = model_with_structured_output.invoke([system_message, human_message])
    
    return {"search_queries": queries.queries}

def map_queries(state: ContextState):
    queries = state.get("search_queries")
    
    return [Send("write_section", {"search_query": query}) for query in queries]

def write_section(state: ContextState) -> ContextState:
    query = state.get("search_query").query
    data = tavily_search.invoke({"query": query})
    results = data.get("results")
    
    formatted_search_docs = "\n\n".join([f"title: {doc.get('title')}\nurl: {doc.get('url')}\ncontent: {doc.get('raw_content')}" for doc in results])
    system_message = SystemMessage(content=SECTION_WRITING_SYSTEM_PROMPT.format(query=query))
    human_message = HumanMessage(content=f"Use and analyze the following documents: {formatted_search_docs}")
    
    section = model.invoke([system_message, human_message])
    
    
    return {"sections": [section.content]}

def final_context(state: ContextState) -> ContextState:
    sections = state.get("sections")
    goal = state.get("goal")
    
    system_message = SystemMessage(content=FINAL_CONTEXT_SYSTEM_PROMPT.format(goal=goal))
    human_message = HumanMessage(content=f"Use and analyze the following memos: {sections}")
    
    final_context = model.invoke([system_message, human_message])
    return {"output_context": final_context.content}

def get_context_graph() -> StateGraph:
    agent = StateGraph(ContextState)
    
    agent.add_node("generate_search_queries", generate_search_queries)
    agent.add_node("write_section", write_section)
    agent.add_node("final_context", final_context)
    
    agent.add_edge(START, "generate_search_queries")
    agent.add_edge("write_section", "final_context")
    agent.add_edge("final_context", END)
    
    agent.add_conditional_edges("generate_search_queries", map_queries)
    
    return agent.compile()
    