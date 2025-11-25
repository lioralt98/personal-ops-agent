from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

class UserPreferences(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    # Identity
    nickname: Optional[str] = Field(default=None)
    pronouns: Optional[str] = Field(default=None)
    timezone: Optional[str] = Field(default="UTC")
    
    # Communication Preferences
    channel_preferences: Optional[str] = Field(default=None)
    summary_preferences: Optional[str] = Field(default=None)
    tone_preferences: Optional[str] = Field(default=None)
    
    # Scheduling Preferences
    meeting_length_default: Optional[int] = Field(default=30)
    buffer_time_default: Optional[int] = Field(default=15)
    reminder_schedule_default: Optional[int] = Field(default=15)
    
    # Notification Preferences
    daily_summary_notification: Optional[bool] = Field(default=False)
    daily_summary_notification_time: Optional[datetime] = Field(default=None)
    
    user: Optional["User"] = Relationship(back_populates="preferences")
    


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    
    token: Optional["Token"] = Relationship(back_populates="user")
    preferences: Optional["UserPreferences"] = Relationship(back_populates="user")