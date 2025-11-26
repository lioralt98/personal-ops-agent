from sqlmodel import Session
import requests
import app.services.tokens as tokens_service
from app.core.config import get_settings

settings = get_settings()

def make_google_request(user_id: int, session: Session, method: str, url: str, **kwargs):
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        response_data = response.json()
        return response_data
    
    except Exception as e:
        print(f"Error making Google request: {e}")
        return None