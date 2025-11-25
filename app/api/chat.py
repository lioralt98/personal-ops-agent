from fastapi import APIRouter, HTTPException
from fastapi.requests import Request

from app.models.chat import ChatMessage
from langchain_core.messages import HumanMessage
from app.core.database import SessionDep
from app.core.config import get_settings
import app.services.users as users_service
import app.services.agent as agent_service
from app.tools.registry import derive_access
import app.services.tokens as tokens_service

settings = get_settings()

router = APIRouter(prefix="/api/chat")

@router.post("/")
def chat(message: ChatMessage, request: Request, session: SessionDep):
    print(message)
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = users_service.get_user(user_id, session)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = tokens_service.get_token_by_user_id(user_id, session)
    scopes = set(token.scope.split(" "))
    user_domains, user_scopes = derive_access(scopes)
    
    agent = agent_service.get_agent(user_scopes, user_domains)
        
    result = agent.invoke(
        {"messages": [HumanMessage(content=message.message)],
         "user_id": user_id,
         },
        {"configurable": {"thread_id": user_id,
                          "session": session}}, 
        )
    last_message = result.get("messages")[-1]
    content = last_message.content
    
    tool_calls = last_message.tool_calls if hasattr(last_message, 'tool_calls') else None
    tool_names = [tool_call.name for tool_call in tool_calls] if tool_calls else None
    
    if isinstance(content, str):
        return {"response": content, "tool_calls": tool_names}
    
    elif isinstance(content, list):
        text_block = content[0]
        
        if isinstance(text_block, dict) and 'text' in text_block:
            return {"response": text_block['text'], "tool_calls": tool_names}

        elif isinstance(text_block, str):
            return {"response": "".join(content), "tool_calls": tool_names}
    
    return {"response": str(content), "tool_calls": tool_names}