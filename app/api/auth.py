from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException

import app.services.oauth as oauth_service
import app.services.users as users_service
import app.services.tokens as tokens_service
from app.models.token import TokenResponse
from app.models.user import User, UserPreferences
from app.models.token import Token
from app.core.database import SessionDep

router = APIRouter(prefix="/auth/oauth2/google")

@router.get("/", response_class=RedirectResponse)
def auth():
    url = oauth_service.get_google_oauth2_url()

    return RedirectResponse(
    url=url,
    status_code=302,
)  

@router.get("/token", response_model=TokenResponse)
def get_token(code: str, request: Request, session: SessionDep) -> TokenResponse:
    token_data = oauth_service.get_token_data_by_code(code)
    access_token = token_data.get("access_token")
    
    user_data = oauth_service.get_google_user_data(access_token)
    user_email = user_data.get("email")
    user_first_name = user_data.get("given_name")
    user_last_name = user_data.get("family_name")
        
    if not user_email:
        raise HTTPException(status_code=404, detail="Email address not found")
    
    user = users_service.get_user_by_email(user_email, session)
    
    if not user:
        user = User(email=user_email, first_name=user_first_name, last_name=user_last_name)
        user = users_service.insert_user(user, session)
        
        preferences = UserPreferences(user_id=user.id)
        users_service.insert_user_preferences(preferences, session)
     
    if not user.token:   
        token = Token(access_token=access_token,
                    expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=token_data.get("expires_in")),
                    user_id=user.id,
                    scope=token_data.get("scope"),
                    refresh_token=token_data.get("refresh_token"),
                    refresh_token_expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=token_data.get("refresh_token_expires_in")),
                    )
        tokens_service.insert_token(token, session)
    
    request.session["user_id"] = user.id
    
    return RedirectResponse(url="/chat", status_code=302)
    

@router.get("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, session: SessionDep) -> TokenResponse:
    user_id = request.session.get("user_id")
    
    token = tokens_service.get_token_by_user_id(user_id=user_id, session=session)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    oauth_service.refresh_token(token_id=token.id, session=session)
    
    return RedirectResponse(url="/chat", status_code=302)
