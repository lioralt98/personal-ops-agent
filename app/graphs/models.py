from typing import List, Optional, Union
from enum import Enum

from sqlmodel import SQLModel, Field

class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class AgentType(str, Enum):
    CONTEXT = "context_agent"
    OPS = "ops_agent"

class UserActionType(str, Enum):
    UPLOAD_FILE = "upload_file"
    APPROVE = "approve"
    PROVIDE_TEXT = "provide_text"
    NONE = "none"

class SearchQuery(SQLModel):
    query: str = Field(description="The search query to be used.")

class SearchQueryList(SQLModel):
    queries: List[SearchQuery] = Field(description="The list of search queries to be used.")

class Resource(SQLModel):
    name: str = Field(description="Key name, e.g., 'sales_csv'")
    path: Optional[str] = Field(None, description="File path or URL if applicable")
    description: str = Field(description="User-facing description of this resource")
    required: bool = Field(description="Whether the resource is required for the step to run.")

class UserConfig(SQLModel):
    action_type: UserActionType = Field(default=UserActionType.NONE, description="The type of action the user is performing.")
    prompt: str = Field(description="Text to show the user, e.g., 'Please upload the sales CSV'")
    required_file_extensions: Optional[List[str]] = Field(default=None, description="The file extensions that are required for the user to upload.")
    output_key: Optional[str] = Field(None, description="Where to store user input in state")

class AgentConfig(SQLModel):
    agent_name: AgentType = Field(description="The name of the agent to be used for the step.")
    task_prompt: str = Field(description="The specific prompt/instruction for the worker agent")
    tool_choice: Optional[str] = Field(None, description="Hint for which tool the agent should prioritize")
    expected_output_key: str = Field(description="Key to store the result in the global state")

class PlanStep(SQLModel):
    id: str = Field(description="The id of the step.")
    title: str = Field(description="Short user-facing title, e.g., 'Analyze CSV'")
    description: str = Field(description="Detailed user-facing explanation")
    status: StepStatus = Field(default=StepStatus.PENDING, description="The status of the step.")
    dependencies: List[str] = Field(default=[], description="IDs of steps that must finish first")
    config: Optional[Union[UserConfig, AgentConfig]] = Field(description="The configuration for the step.")
    required_resources: List[Resource] = Field(default=[], description="Resources needed before this step can run")

class Plan(SQLModel):
    steps: List[PlanStep] = Field(description="The steps to be completed.")