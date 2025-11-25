from typing import Optional, List

from sqlmodel import SQLModel

class Link(SQLModel):
    type: str
    description: str
    link: str

class Task(SQLModel):
    id: Optional[int]
    title: str
    status: str
    notes: Optional[str]
    completed: Optional[str]
    updated: Optional[str]
    links: Optional[List[Link]]

class TaskList(SQLModel):
    id: Optional[int]
    title: str
    updated: Optional[str]
    
    
    