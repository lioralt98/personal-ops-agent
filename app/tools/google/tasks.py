from typing import List, Annotated

from sqlmodel import Session
import requests
from langchain.tools import tool, BaseTool
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig

import app.services.tokens as tokens_service
from app.core.config import get_settings
from app.models.tasks import TaskList, Task

settings = get_settings()

@tool
def insert_tasklist(tasklist: TaskList, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> TaskList:
    """Create a new task list to organize related tasks.

    Use this tool when the user explicitly wants to create a separate category or list for tasks (e.g., "Create a shopping list" or "New project tasks").
    
    Args:
        tasklist: A TaskList object containing the properties for the new list. The 'title' field is mandatory.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        TaskList: The created task list object with its assigned ID and metadata.

    Note:
        Do NOT use this for creating individual tasks; use `insert_task` for that. If the operation fails, return None.
    """
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.post(f"{settings.google_tasks_tasklist_endpoint}",
                             json=tasklist.model_dump(),
                             headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error inserting tasklist: {e}")
        return None
    tasklist_data = response.json()
    tasklist = TaskList.model_validate(tasklist_data)
    
    return tasklist


@tool
def get_tasklist(tasklist_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> TaskList:
    """Retrieve metadata for a specific task list by its unique ID.

    Use this to verify if a list exists or to get its current title/etag before updating.

    Args:
        tasklist_id: The unique identifier of the task list (e.g., from `list_tasklists`).
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        TaskList: The task list object if found, otherwise None.

    Note:
        If the task list is not found, handle the error gracefully and return None.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }

    try:
        response = requests.get(f"{settings.google_tasks_get_tasklist_endpoint}/{tasklist_id}",
                            headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error getting tasklist: {e}")
        return None
    tasklist_data = response.json()
    tasklist = TaskList.model_validate(tasklist_data)
    
    return tasklist

@tool
def list_tasklists(user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> List[TaskList]:
    """List all available task lists for the user.

    Retrieves all task lists (categories) to help identify the correct list ID for other operations.

    Args:
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        List[TaskList]: A list of TaskList objects containing 'id' and 'title'.

    Note:
        ALWAYS call this tool first when the user refers to a list by name (e.g., "my shopping list") to find its corresponding `tasklist_id`.
        If no lists are found, returns an empty list.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.get(f"{settings.google_tasks_get_tasklist_endpoint}",
                            headers=headers)
        response.raise_for_status()
    
    except Exception as e:
        print(f"Error listing tasklists: {e}")
        return []
        
    tasklist_list_data = response.json()
    tasklists = []
    
    for tl in tasklist_list_data:
        tasklists.append(TaskList.model_validate(tl).model_dump())
    
    return tasklists

@tool
def update_tasklist(tasklist_id: str, tasklist: TaskList, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> TaskList:
    """Update the properties of an existing task list.

    Modifies metadata such as the title of a specific task list.

    Args:
        tasklist_id: The unique identifier of the task list to update.
        tasklist: The TaskList object with the new properties (e.g., a new 'title').
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        TaskList: The updated task list object.

    Note:
        Ensure the `tasklist_id` is valid before attempting update.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.put(f"{settings.google_tasks_tasklist_endpoint}/{tasklist_id}",
                            json=tasklist.model_dump(),
                            headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error updating tasklist: {e}")
        return None
    
    tasklist_data = response.json()
    tasklist = TaskList.model_validate(tasklist_data)
    
    return tasklist

@tool
def delete_tasklist(tasklist_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig):
    """Permanently delete a task list and ALL tasks contained within it.

    Removes a task list and every task contained within it. This action is irreversible.

    Args:
        tasklist_id: The unique identifier of the task list to delete.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        None

    Note:
        Use with caution. Ask for user confirmation if the list might contain important items.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.delete(f"{settings.google_tasks_tasklist_endpoint}/{tasklist_id}",
                                headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error deleting tasklist: {e}")
        return None
    

@tool
def insert_task(task: Task, tasklist_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> Task:
    """Create a new task within a specific task list.

    Adds a new task item to the specified list.

    Args:
        task: The Task object. Required fields: 'title'. Optional: 'notes', 'due' (RFC 3339 timestamp).
        tasklist_id: The ID of the target list. Use '@default' for the user's default list, or an ID from `list_tasklists`.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        Task: The created task object.

    Note:
        If `tasklist_id` is not provided, default to '@default'.
    """

    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.post(f"{settings.google_tasks_task_endpoint}/{tasklist_id}/tasks",
                             json=task.model_dump(),
                             headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error inserting task: {e}")
        return None
    task_data = response.json()
    task = Task.model_validate(task_data)
    
    return task

@tool
def get_task(task_id: str, tasklist_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> Task:
    """Retrieve details of a specific task.

    Fetches the full properties of a task, including status, due date, and notes.

    Args:
        task_id: The unique identifier of the task.
        tasklist_id: The ID of the list containing the task (or '@default').
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        Task: The requested task object.

    Note:
        If the task is not found, return None.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.get(f"{settings.google_tasks_task_endpoint}/{tasklist_id}/tasks/{task_id}",
                            headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error getting task: {e}")
        return None
    task_data = response.json()
    task = Task.model_validate(task_data)
    
    return task

@tool
def list_tasks(tasklist_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> List[Task]:
    """List all tasks within a specific task list.

    Retrieves all tasks from a given list, useful for searching, checking status, or summarizing.
    
    Args:
        tasklist_id: The ID of the list to fetch. Use '@default' for the main list or an ID from `list_tasklists`.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        List[Task]: A list of Task objects from the specified list.

    Note:
        Returns an empty list if the task list is empty or not found.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.get(f"{settings.google_tasks_task_endpoint}/{tasklist_id}/tasks",
                            headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error listing tasks: {e}")
        return []
    task_list_data = response.json()
    tasks = []
    
    for t in task_list_data:
        tasks.append(Task.model_validate(t))
        
    return tasks

@tool
def update_task(task_id: str, task: Task, tasklist_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig) -> Task:
    """Update an existing task's properties.

    Modifies a task's details, such as marking it as complete, changing the title, or updating the due date.

    Args:
        task_id: The unique identifier of the task to update.
        task: The updated Task object. To complete a task, set 'status' to 'completed'.
        tasklist_id: The ID of the list containing the task.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        Task: The updated task object.

    Note:
        Ensure you have the latest task version before updating.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.put(f"{settings.google_tasks_task_endpoint}/{tasklist_id}/tasks/{task_id}",
                            json=task.model_dump(),
                            headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error updating task: {e}")
        return None
    task_data = response.json()
    task = Task.model_validate(task_data)
    
    return task

@tool
def delete_task(task_id: str, tasklist_id: str, user_id: Annotated[str, InjectedState("user_id")], config: RunnableConfig):
    """Permanently delete a specific task.

    Removes a task from its task list. This cannot be undone.

    Args:
        task_id: The unique identifier of the task.
        tasklist_id: The ID of the list containing the task.
        user_id: Injected user ID.
        config: Injected configuration.

    Returns:
        None

    Note:
        If the task does not exist, log the error and return None.
    """
    
    session = config["configurable"]["session"]
    db_token = tokens_service.get_token_by_user_id(user_id, session)
    headers = {
        "Authorization": f"Bearer {db_token.access_token}"
    }
    try:
        response = requests.delete(f"{settings.google_tasks_task_endpoint}/{tasklist_id}/tasks/{task_id}",
                            headers=headers)
        response.raise_for_status()
        
    except Exception as e:
        print(f"Error deleting task: {e}")
        return None

def get_tools():
    tools = []
    
    for obj in globals().values():
        if isinstance(obj, BaseTool):
            tools.append(obj)
    
    return tools