from typing import List, Annotated

from langchain.tools import tool, BaseTool
from sqlmodel import Session
import requests
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig

from app.models.calendar import CalendarEvent
from app.core.config import get_settings
import app.services.tokens as tokens_service

settings = get_settings()

@tool
def insert_event(event: CalendarEvent, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> CalendarEvent:
    """Create a new calendar event in the user's primary calendar.

    Schedules a new event with a title, start time, and end time.

    Args:
        event: The CalendarEvent object containing event details.
               Required fields:
               - 'summary': The title of the event.
               - 'start': Object with 'dateTime' (ISO 8601 string, e.g., "2023-10-27T10:00:00Z").
               - 'end': Object with 'dateTime' (ISO 8601 string).
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        CalendarEvent: The created event object with assigned ID.

    Note:
        Ensure start time is before end time. 
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    response = requests.post(f"{settings.google_calendar_events_endpoint}",
                             json=event.model_dump(),
                             headers=headers)
    
    response.raise_for_status()
    event_data = response.json()
    event = CalendarEvent.model_validate(event_data)
    
    return event

@tool
def get_event(event_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> CalendarEvent:
    """Retrieve full details of a specific calendar event.

    Fetches metadata for an event, including description, location, and attendees.

    Args:
        event_id: The unique identifier of the event (retrieved from list_events or insert_event).
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        CalendarEvent: The requested event object.

    Note:
        If the event is not found, raise an error or return None.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    response = requests.get(f"{settings.google_calendar_events_endpoint}/{event_id}",
                             headers=headers)
    
    response.raise_for_status()
    event_data = response.json()
    event = CalendarEvent.model_validate(event_data)
    
    return event

@tool
def list_events(user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> List[CalendarEvent]:
    """List upcoming calendar events from the user's primary calendar.

    Retrieves a list of future events, useful for checking availability or finding specific events to modify.

    Args:
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        List[CalendarEvent]: A list of upcoming calendar events.

    Note:
        This tool returns events from the 'primary' calendar. 
        If no events are found, returns an empty list.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    response = requests.get(f"{settings.google_calendar_events_endpoint}",
                             headers=headers)
    
    response.raise_for_status()
    event_list_data = response.json().get("items")
    events = []
    
    if event_list_data:
        for e in event_list_data:
            events.append(CalendarEvent.model_validate(e))
    
    return events

@tool
def update_event(event_id: str, event: CalendarEvent, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> CalendarEvent:
    """Update an existing calendar event.

    Modifies event details such as rescheduling (start/end times), renaming, or changing description.

    Args:
        event_id: The unique identifier of the event to update.
        event: The updated CalendarEvent object. Ensure start/end times are valid ISO 8601 strings.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        CalendarEvent: The updated event object.

    Note:
        Ensure the `event_id` matches the event being updated.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    response = requests.put(f"{settings.google_calendar_events_endpoint}/{event_id}",
                             json=event.model_dump(),
                             headers=headers)
    
    response.raise_for_status()
    event_data = response.json()
    event = CalendarEvent.model_validate(event_data)
    
    return event

@tool
def delete_event(event_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> None:
    """Permanently delete a calendar event.

    Removes an event from the calendar. This action is irreversible.

    Args:
        event_id: The unique identifier of the event to delete.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        None

    Note:
        If the event does not exist, handle gracefully.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    response = requests.delete(f"{settings.google_calendar_events_endpoint}/{event_id}",
                             headers=headers)
    
    response.raise_for_status()

def get_tools():
    tools = []
    
    for obj in globals().values():
        if isinstance(obj, BaseTool):
            tools.append(obj)
    
    return tools