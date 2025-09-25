"""
Background task processing and queue management
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timezone
from enum import Enum
import uuid
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BackgroundTask:
    """Background task definition"""
    id: str
    name: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Any = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class BackgroundTaskManager:
    """Enhanced background task manager"""
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.task_queue = asyncio.Queue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.workers: List[asyncio.Task] = []
        self.max_workers = 3
        self.is_running = False
    
    async def start(self):
        """Start the task manager"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"Starting {self.max_workers} background task workers")
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Stop the task manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping background task manager")
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"Cancelled running task: {task_id}")
        
        self.running_tasks.clear()
    
    async def add_task(
        self,
        name: str,
        function: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """Add a new background task"""
        task_id = str(uuid.uuid4())
        
        task = BackgroundTask(
            id=task_id,
            name=name,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        await self.task_queue.put(task)
        
        logger.info(f"Added background task: {name} (ID: {task_id})")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and details"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        result = {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
        }
        
        # Include result if completed successfully
        if task.status == TaskStatus.COMPLETED and task.result is not None:
            try:
                # Try to serialize result
                json.dumps(task.result)
                result["result"] = task.result
            except (TypeError, ValueError):
                result["result"] = str(task.result)
        
        return result
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # If task is running, cancel the asyncio task
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc)
        
        logger.info(f"Cancelled task: {task.name} (ID: {task_id})")
        return True
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue and worker status"""
        return {
            "is_running": self.is_running,
            "queue_size": self.task_queue.qsize(),
            "active_workers": len(self.workers),
            "running_tasks": len(self.running_tasks),
            "total_tasks": len(self.tasks),
            "task_counts": {
                status.value: len([t for t in self.tasks.values() if t.status == status])
                for status in TaskStatus
            }
        }
    
    async def _worker(self, worker_name: str):
        """Background worker to process tasks"""
        logger.info(f"Background worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get next task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Update task status
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now(timezone.utc)
                
                logger.info(f"Worker {worker_name} processing task: {task.name} (ID: {task.id})")
                
                # Create asyncio task for execution
                execution_task = asyncio.create_task(self._execute_task(task))
                self.running_tasks[task.id] = execution_task
                
                try:
                    # Execute the task
                    await execution_task
                    
                except asyncio.CancelledError:
                    logger.info(f"Task cancelled: {task.name} (ID: {task.id})")
                    task.status = TaskStatus.CANCELLED
                
                finally:
                    # Cleanup
                    if task.id in self.running_tasks:
                        del self.running_tasks[task.id]
                    
                    task.completed_at = datetime.now(timezone.utc)
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
        
        logger.info(f"Background worker {worker_name} stopped")
    
    async def _execute_task(self, task: BackgroundTask):
        """Execute a single task with retry logic"""
        for attempt in range(task.max_retries + 1):
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(task.function):
                    result = await task.function(*task.args, **task.kwargs)
                else:
                    # Run sync function in executor
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, task.function, *task.args
                    )
                
                # Task completed successfully
                task.status = TaskStatus.COMPLETED
                task.result = result
                
                logger.info(f"Task completed successfully: {task.name} (ID: {task.id})")
                return
                
            except Exception as e:
                task.retry_count = attempt + 1
                error_msg = f"Attempt {attempt + 1}/{task.max_retries + 1} failed: {str(e)}"
                logger.warning(f"Task {task.name} (ID: {task.id}) - {error_msg}")
                
                if attempt < task.max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = min(2 ** attempt, 60)  # Max 60 seconds
                    await asyncio.sleep(wait_time)
                else:
                    # Max retries reached
                    task.status = TaskStatus.FAILED
                    task.error_message = f"Failed after {task.max_retries + 1} attempts. Last error: {str(e)}"
                    logger.error(f"Task failed permanently: {task.name} (ID: {task.id}) - {task.error_message}")
                    return


# Global task manager instance
task_manager = BackgroundTaskManager()


# Convenience functions for common background tasks
async def process_bulk_todos(todo_ids: List[int], action: str):
    """Example bulk processing function"""
    logger.info(f"Processing {len(todo_ids)} todos with action: {action}")
    
    # Simulate processing
    for todo_id in todo_ids:
        await asyncio.sleep(0.1)  # Simulate work
        logger.debug(f"Processed todo {todo_id}")
    
    return f"Successfully processed {len(todo_ids)} todos"


async def generate_report(report_type: str, filters: Dict[str, Any]):
    """Example report generation function"""
    logger.info(f"Generating {report_type} report with filters: {filters}")
    
    # Simulate report generation
    await asyncio.sleep(2)
    
    return f"Report generated: {report_type}"


async def cleanup_old_data(days_old: int = 30):
    """Example cleanup function"""
    logger.info(f"Cleaning up data older than {days_old} days")
    
    # Simulate cleanup
    await asyncio.sleep(1)
    
    return f"Cleaned up data older than {days_old} days"