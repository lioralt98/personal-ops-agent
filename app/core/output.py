from typing import Optional, List

from datetime import datetime
from sqlmodel import SQLModel, Field

class ChatInsights(SQLModel):
    # Identity
    nickname: Optional[str] = Field(default=None, description="The user's preferred nickname.")
    pronouns: Optional[str] = Field(default=None, description="The user's preferred pronouns (e.g. he/him, she/her, they/them).")
    timezone: Optional[str] = Field(default=None, description="The user's timezone (IANA format, e.g. 'America/New_York').")
    
    # Communication Preferences
    channel_preferences: Optional[List[str]] = Field(default=None, description="Preferred communication channels (e.g. email, slack, whatsapp).")
    summary_preferences: Optional[str] = Field(default=None, description="How the user prefers summaries (e.g. bullet points, brief, detailed).")
    tone_preferences: Optional[str] = Field(default=None, description="The user's preferred tone of communication (e.g. formal, casual, concise).")
    
    # Scheduling Preferences
    meeting_length_default: Optional[int] = Field(default=30, description="Default duration for meetings in minutes.")
    buffer_time_default: Optional[int] = Field(default=15, description="Default buffer time between meetings in minutes.")
    reminder_schedule_default: Optional[int] = Field(default=15, description="Default reminder time before events in minutes.")
    
    # Notification Preferences
    daily_summary_notification: Optional[bool] = Field(default=False, description="Whether the user wants a daily summary notification.")
    daily_summary_notification_time: Optional[datetime] = Field(default=None, description="The time of day to send the daily summary notification (ISO 8601 format).")
