import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from sqlmodel import Session

from app.models.token import Token
import app.services.tokens as tokens_service
from app.core.config import get_settings

settings = get_settings()

def get_google_oauth2_url() -> str:
    params = {
        
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "response_type": "code",
            "scope": settings.scope,
            'access_type': 'offline',
            "prompt": "consent",
        }
    
    url = f"{settings.google_auth_endpoint}?{urlencode(params)}"
    return url

def get_token_data_by_code(code: str) -> dict:
    params = {
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.redirect_uri,
        }
    response = requests.post(settings.google_token_endpoint, json=params)
    response.raise_for_status()
    token_data = response.json()
    
    return token_data

def get_google_user_data(access_token: str) -> str:
    params = {
        "Authorization": f"Bearer {access_token}",
    }
    
    response = requests.get(settings.google_userinfo_endpoint, headers=params, timeout=10)
    response.raise_for_status()
    user_data = response.json()
    
    return user_data

def refresh_token(token_id: int, session: Session) -> Token:
    token = tokens_service.get_token(token_id, session)
    
    params = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "refresh_token": token.get_refresh_token,
        "grant_type": "refresh_token",
    }
    
    response = requests.post(settings.google_token_endpoint, data=params)
    response.raise_for_status()
    
    token_data = response.json()
    token_updates = Token(access_token=token_data.get("access_token"),
                          expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=token_data.get("expires_in")),
                          refresh_token=token_data.get("refresh_token"),
                          refresh_token_expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=token_data.get("refresh_token_expires_in")),
                          scope=token_data.get("scope"),
                          )
    token = tokens_service.update_token(token_id, token_updates, session)
    
    return token
    
    