from typing import Optional, Union
from sqlmodel import Session, select

from app.models.user import User, UserPreferences
from app.core.output import ChatInsights

def insert_user(user: User, session: Session) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user

def get_user(user_id: int, session: Session) -> User:
    return session.get(User, user_id)

def get_user_by_email(email: str, session: Session) -> User:
    query = select(User).where(User.email == email)
    user = session.exec(query).first()
    
    return user

def insert_user_preferences(preferences: UserPreferences, session: Session) -> UserPreferences:
    session.add(preferences)
    session.commit()
    session.refresh(preferences)
    
    return preferences

def get_user_preferences(user_id: int, session: Session) -> UserPreferences:
    query = select(UserPreferences).where(UserPreferences.user_id == user_id)
    preferences = session.exec(query).first()
    
    return preferences

def update_user_preferences(preferences_id: int, preferences: Union[UserPreferences, ChatInsights], session: Session) -> Optional[UserPreferences]:
    db_preferences = session.get(UserPreferences, preferences_id)
    updates = preferences.model_dump(exclude_unset=True)
    
    db_preferences.sqlmodel_update(updates)
    session.add(db_preferences)
    session.commit()
    session.refresh(db_preferences)
    
    return db_preferences