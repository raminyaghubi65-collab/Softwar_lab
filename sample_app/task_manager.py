"""A tiny in-memory task manager used as a software-testing sample."""

from dataclasses import dataclass


@dataclass
class Task:
    task_id: int
    title: str
    completed: bool = False


class TaskManager:
    """Manage tasks in memory; task IDs must be unique positive integers."""

    def __init__(self):
        self._tasks = {}

    def add_task(self, task_id: int, title: str) -> Task:
        if not isinstance(task_id, int) or isinstance(task_id, bool) or task_id <= 0:
            raise ValueError("task_id must be a positive integer")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        if task_id in self._tasks:
            raise ValueError(f"task {task_id} already exists")

        task = Task(task_id=task_id, title=title.strip())
        self._tasks[task_id] = task
        return task

    def complete_task(self, task_id: int) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"task {task_id} was not found")
        self._tasks[task_id].completed = True
        return self._tasks[task_id]

    def get_task(self, task_id: int) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"task {task_id} was not found")
        return self._tasks[task_id]

    def list_tasks(self):
        return list(self._tasks.values())
