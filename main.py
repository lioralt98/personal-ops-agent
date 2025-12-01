import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse

from app.core.database import create_db_and_tables, SessionDep
from app.api import auth, chat
import app.services.tokens as tokens_service


load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_MIDDLEWARE_SECRET_KEY"),
)
    

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
def login_page(request: Request):
    user_id = request.session.get("user_id")
    
    if user_id:
        return RedirectResponse(url="/chat", status_code=302)
    
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/chat")
def chat_page(request: Request, session: SessionDep):
    user_id = request.session.get("user_id")
    
    if not user_id:
        return RedirectResponse(url="/", status_code=302)
    
    token = tokens_service.get_token_by_user_id(user_id, session)
    
    if not token:
        request.session.clear()
        return RedirectResponse(url="/", status_code=302)
    
    refresh_token_expires_at = token.refresh_token_expires_at.replace(tzinfo=timezone.utc)
    
    if refresh_token_expires_at < datetime.now(tz=timezone.utc):
        request.session.clear()
        return RedirectResponse(url="/", status_code=302)
    
    access_token_expires_at = token.expires_at.replace(tzinfo=timezone.utc)
    
    if access_token_expires_at < datetime.now(tz=timezone.utc):
        return RedirectResponse(url="/auth/oauth2/google/refresh")
    
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/editor")
def editor_page(request: Request):
    return templates.TemplateResponse("editor.html", {"request": request})