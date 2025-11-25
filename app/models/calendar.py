from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel


class EventTime(SQLModel):
    date: Optional[datetime] = None
    dateTime: Optional[datetime] = None
    timeZone: Optional[str] = None

class Attendee(SQLModel):
    email: str
    displayName: str
    responseStatus: str
    
class CalendarEvent(SQLModel):
    id: Optional[int]
    status: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    location: Optional[str]
    start: EventTime
    end: EventTime
    attendees: Optional[List[Attendee]]
    