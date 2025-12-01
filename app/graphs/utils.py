from collections import defaultdict, deque
from typing import Tuple

from app.graphs.models import Plan, Task

def is_plan_dag(plan: Plan) -> Tuple[bool, str]:
    adj = defaultdict(list)
    task_ids = set([task.task_id for task in plan.tasks])
    in_degree = defaultdict(int)
    
    for task in plan.tasks:
        dep_set = set(task.dependencies)
        if len(dep_set) != len(task.dependencies):
            return False, f"Error: Dependencies IDs in task {task.task_id} are not unique."
        if not dep_set.issubset(task_ids):
            return False, f"Error: One or more dependencies IDs from task {task.task_id} are not found in tasks."

        for dep in dep_set:
            adj[dep].append(task.task_id)
            in_degree[task.task_id] += 1
    
    q = deque([task_id for task_id in adj.keys() if in_degree[task_id] == 0])
    visited_tasks = 0
    
    while q:
        cur_task_id = q.popleft()
        visited_tasks += 1
        
        for nei in adj[cur_task_id]:
            in_degree[nei] -= 1
            if in_degree[nei] == 0:
                q.append(nei)
    
    if visited_tasks < len(adj):
        return False, "Error: The plan contains a cycle."
    return True, "Success: The plan is a DAG."
    