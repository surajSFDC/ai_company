"""Task queue for parallel execution."""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
import threading


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A task in the queue"""

    id: str
    name: str
    description: str
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    approval_required: bool = False
    approval_status: Optional[str] = None


class TaskQueue:
    """Queue for managing parallel task execution"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.tasks: Dict[str, Task] = {}
        self.pending_queue: List[str] = []
        self.running_tasks: Dict[str, Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()

        self.on_task_complete: Optional[Callable] = None
        self.on_task_fail: Optional[Callable] = None
        self.on_approval_needed: Optional[Callable] = None

    def add_task(
        self,
        name: str,
        description: str,
        task_type: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        context: Dict[str, Any] = None,
        dependencies: List[str] = None,
        approval_required: bool = False,
    ) -> str:
        """Add a task to the queue"""
        task_id = str(uuid.uuid4())[:8]

        task = Task(
            id=task_id,
            name=name,
            description=description,
            task_type=task_type,
            priority=priority,
            context=context or {},
            dependencies=dependencies or [],
            approval_required=approval_required,
        )

        with self.lock:
            self.tasks[task_id] = task
            self.pending_queue.append(task_id)
            self.pending_queue.sort(
                key=lambda t: self.tasks[t].priority.value,
                reverse=True,
            )

        return task_id

    def get_next_task(self) -> Optional[Task]:
        """Get the next task that's ready to run"""
        with self.lock:
            for task_id in self.pending_queue:
                task = self.tasks[task_id]
                deps_met = all(
                    self.tasks.get(dep_id)
                    and self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if deps_met:
                    return task
            return None

    def start_task(self, task_id: str, executor: Callable) -> Future:
        """Start executing a task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        with self.lock:
            if task_id in self.pending_queue:
                self.pending_queue.remove(task_id)
            self.running_tasks[task_id] = task

        future = self.executor.submit(self._execute_task, task_id, executor)
        return future

    def _execute_task(self, task_id: str, executor: Callable) -> Any:
        """Execute a task"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        try:
            result = executor(task)
            task.result = result

            if task.approval_required:
                task.status = TaskStatus.WAITING_APPROVAL
                if self.on_approval_needed:
                    self.on_approval_needed(task)
            else:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                with self.lock:
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]
                if self.on_task_complete:
                    self.on_task_complete(task)

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            with self.lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
            if self.on_task_fail:
                self.on_task_fail(task, e)
            raise

    def approve_task(self, task_id: str, approved: bool = True, skip: bool = False):
        """Approve or reject a task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if skip:
            task.approval_status = "skipped"
        elif approved:
            task.approval_status = "approved"
        else:
            task.approval_status = "rejected"

        if task.approval_status in ["approved", "skipped"]:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            with self.lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
            if self.on_task_complete:
                self.on_task_complete(task)
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            if self.on_task_fail:
                self.on_task_fail(task, Exception("Task rejected"))

    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of queue status"""
        return {
            "total": len(self.tasks),
            "pending": len(self.pending_queue),
            "running": len(self.running_tasks),
            "completed": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
            ),
            "waiting_approval": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.WAITING_APPROVAL]
            ),
            "failed": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
            ),
        }

    def shutdown(self) -> None:
        """Shutdown the executor"""
        self.executor.shutdown(wait=True)

