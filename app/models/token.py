from typing import Optional
from datetime import datetime

from sqlalchemy import TEXT
from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator

from app.core.security import encrypt_refresh_token, decrypt_refresh_token

class Token(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    refresh_token: str = Field(sa_type=TEXT)
    access_token: str
    expires_at: datetime
    refresh_token_expires_at: datetime
    scope: str
    
    user: Optional["User"] = Relationship(back_populates="token")
    
    @field_validator("refresh_token", mode="before")
    @classmethod
    def encrypt_refresh_token(cls, v: str) -> str:
        return encrypt_refresh_token(v)
    
    @property
    def get_refresh_token(self) -> str:
        return decrypt_refresh_token(self.refresh_token)

class TokenResponse(SQLModel):
    access_token: str
    expires_at: datetime