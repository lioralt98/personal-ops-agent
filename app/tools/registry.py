from typing import List, NamedTuple

import importlib

class Toolset(NamedTuple):
    module: str
    getter: str
    domain: str
    required_scope: str
    
TOOL_REGISTRY: List[Toolset] = [
    Toolset("app.tools.google.tasks",
            "get_tools",
            "tasks",
            "https://www.googleapis.com/auth/tasks"
            ),
    Toolset("app.tools.google.calendar",
            "get_tools",
            "calendar",
            "https://www.googleapis.com/auth/calendar"
            ),
]

def load_tools(user_scopes: set[str], user_domains: set[str]):
    tools = []
    
    for toolset in TOOL_REGISTRY:
        if toolset.domain not in user_domains or toolset.required_scope not in user_scopes:
            continue
        
        module = importlib.import_module(toolset.module)
        getter = getattr(module, toolset.getter)
        tools.extend(getter())
    
    return tools

def derive_access(scopes: set[str]) -> tuple[set[str], set[str]]:
    user_domains = set()
    user_scopes = set()
    
    for toolset in TOOL_REGISTRY:
        if toolset.required_scope in scopes:
            user_domains.add(toolset.domain)
            user_scopes.add(toolset.required_scope)
    
    return user_domains, user_scopes