from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph

from app.graphs.state import State
from app.core.config import get_settings
from app.graphs.models import SearchQuery

settings = get_settings()
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
                              google_api_key=settings.gemini_api_key,
                              temperature=0)
tavily_search = TavilySearchResults(max_results=3)

QUERY_SYSTEM_PROMPT = """
You are a helpful assistant that can help the user with their research.
You will be given a task and you will need to generate a search query to help the user with their research.
"""

def get_search_query(state: State) -> State:
    query_system_message = SystemMessage(content=QUERY_SYSTEM_PROMPT.format())
    model_with_structured_output = model.with_structured_output(SearchQuery)
    
    result = model.invoke([query_system_message])
    return {"search_query": result.content}

def research(state: State) -> State:
    search_query = state.get("search_query")
    search_docs = tavily_search.invoke(search_query)
    return {"search_docs": search_docs}

def get_researcher_graph() -> StateGraph:
    pass