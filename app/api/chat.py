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
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = users_service.get_user(user_id, session)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = tokens_service.get_token_by_user_id(user_id, session)
    scopes = set(token.scope.split(" "))
    user_domains, user_scopes = derive_access(scopes)
    
    agent = get_supervisor_graph(user_scopes, user_domains)
    config = {"configurable": {"thread_id": user_id,
                              "session": session}}
    
    for chunk in agent.stream({
        "goal": message.message,
        "user_id": user_id,
        },
     stream_mode="values",
     config=config,
    ):
        print(chunk)
    
    state = agent.get_state(config=config)
    print(f"\n\n\nINTERRUPTED:\n{state}")
    
    if state.next:
        return {"steps": state.tasks[0].interrupts[0].value["steps"]}
                              
     
    