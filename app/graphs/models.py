from typing import List, Optional, Literal

from sqlmodel import SQLModel, Field

class Task(SQLModel):
    task_id: str = Field(description="The id of the task.")
    title: str = Field(description="The title of the task.")
    reasoning: str = Field(description="The reasoning for the task.")
    task_dest: Literal["user", "agent"] = Field(description="The destination of the task.")
    dependencies: List[str] = Field(description="The dependencies ids of the task.")

class Plan(SQLModel):
    tasks: List[Task] = Field(description="The tasks to be completed.")


class SearchQuery(SQLModel):
    query: str = Field(description="The search query to be used.")
    