from fastapi import APIRouter, HTTPException
from fastapi.requests import Request

from app.models.chat import ChatMessage
from langchain_core.messages import HumanMessage
from app.core.database import SessionDep
from app.core.config import get_settings
import app.services.users as users_service
from app.tools.registry import derive_access
import app.services.tokens as tokens_service
from app.graphs.supervisor import get_supervisor_graph
from langgraph.types import Command

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
    
    agent = get_supervisor_graph()
    config = {"configurable": {"thread_id": user_id,
                              "session": session}}
    state = agent.get_state(config=config)
    
    if state.next:
        user_plan = agent.invoke(Command(resume=message.message), config=config)
    
    else:
        user_plan = agent.invoke(
            {"human_feedback": [HumanMessage(content=message.message)],
            "user_id": user_id,
            },
            config=config, 
            )
        
    print(user_plan) 
    return {"user_plan": user_plan}
     
    