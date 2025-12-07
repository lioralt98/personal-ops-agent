from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    db_url: str
    fernet_encryption_key: str
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_model_name: str = "gemini-2.5-flash"
    tavily_api_key: str | None = None
    langsmith_api_key: str | None = None
    langsmith_tracing: bool
    session_middleware_secret_key: str
    
    google_auth_endpoint: str
    google_token_endpoint: str
    google_userinfo_endpoint: str
    google_tasks_tasklist_endpoint: str
    google_tasks_task_endpoint: str
    google_calendar_events_endpoint: str
    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    return Settings()