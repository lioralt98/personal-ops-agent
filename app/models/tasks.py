from typing import Optional, List

from sqlmodel import SQLModel

class Link(SQLModel):
    type: str
    description: str
    link: str

class Task(SQLModel):
    id: Optional[str]
    title: str
    status: str
    notes: Optional[str] = None
    completed: Optional[str] = None
    updated: Optional[str] = None
    links: Optional[List[Link]] = None

class TaskList(SQLModel):
    id: Optional[str]
    title: str
    updated: Optional[str] = None
    
    
    