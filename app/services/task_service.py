from typing import List, Optional
from datetime import date, datetime, timezone, timedelta
from sqlmodel import Session, select

from app.models.task import Task
from app.models.goal import Goal
from app.schemas.task import TaskCreate, TaskUpdate, CompletionStatusEnum, TaskDiscard, TaskRestore


def create_task(session: Session, data: TaskCreate) -> Task:
    task = Task(
        user_id=data.user_id,
        goal_id=data.goal_id,
        description=data.description,
        priority=data.priority,
        ai_generated=bool(getattr(data, "ai_generated", False)),
        completion_status=data.completion_status,
        estimated_duration=data.estimated_duration,
        actual_duration=data.actual_duration,
        energy_required=data.energy_required,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def list_tasks(
    session: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    goal_id: Optional[int] = None,
    completion_status: Optional[CompletionStatusEnum] = None,
    include_discarded: bool = False,
) -> List[Task]:
    statement = select(Task)
    if user_id:
        statement = statement.where(Task.user_id == user_id)
    if goal_id:
        statement = statement.where(Task.goal_id == goal_id)
    if completion_status:
        statement = statement.where(Task.completion_status == completion_status)
    elif not include_discarded:
        # Exclude discarded tasks by default unless specifically requested
        statement = statement.where(Task.completion_status != CompletionStatusEnum.DISCARDED)
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()


def get_task(session: Session, task_id: int) -> Optional[Task]:
    return session.get(Task, task_id)


def update_task(session: Session, task_id: int, update: TaskUpdate) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise LookupError("Task not found")
    data = update.model_dump(exclude_unset=True)

    if data.get("goal_id") is not None:
        goal = session.get(Goal, data["goal_id"])
        if not goal:
            raise LookupError("Goal not found")
        if goal.user_id != task.user_id:
            raise ValueError("Goal does not belong to the task's user")

    for field, value in data.items():
        setattr(task, field, value)
    
    # Update the updated_at timestamp using system default timezone
    task.updated_at = datetime.now()
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def discard_task(session: Session, task_id: int, discard_data: TaskDiscard) -> Task:
    """Discard a task with a message explaining why it was discarded."""
    task = session.get(Task, task_id)
    if not task:
        raise LookupError("Task not found")
    
    if task.completion_status == CompletionStatusEnum.DISCARDED:
        raise ValueError("Task is already discarded")
    
    task.completion_status = CompletionStatusEnum.DISCARDED
    task.discard_message = discard_data.discard_message
    task.updated_at = datetime.now()
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def restore_task(session: Session, task_id: int, restore_data: Optional[TaskRestore] = None) -> Task:
    """Restore a discarded task back to pending status."""
    task = session.get(Task, task_id)
    if not task:
        raise LookupError("Task not found")
    
    if task.completion_status != CompletionStatusEnum.DISCARDED:
        raise ValueError("Task is not discarded")
    
    task.completion_status = CompletionStatusEnum.PENDING
    task.discard_message = None
    task.updated_at = datetime.now()
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def list_discarded_tasks(
    session: Session,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Task]:
    """List only discarded tasks."""
    statement = select(Task).where(Task.completion_status == CompletionStatusEnum.DISCARDED)
    if user_id:
        statement = statement.where(Task.user_id == user_id)
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()


def delete_task(session: Session, task_id: int) -> None:
    task = session.get(Task, task_id)
    if not task:
        raise LookupError("Task not found")
    session.delete(task)
    session.commit()


def list_user_tasks(session: Session, user_id: str, include_discarded: bool = False) -> List[Task]:
    statement = select(Task).where(Task.user_id == user_id)
    if not include_discarded:
        statement = statement.where(Task.completion_status != CompletionStatusEnum.DISCARDED)
    return session.exec(statement).all()


def list_user_today_tasks(session: Session, user_id: str, include_discarded: bool = False) -> List[Task]:
    # Since we removed deadline, this function now returns all user tasks
    # You may want to implement different logic based on your requirements
    statement = select(Task).where(Task.user_id == user_id)
    if not include_discarded:
        statement = statement.where(Task.completion_status != CompletionStatusEnum.DISCARDED)
    return session.exec(statement).all()


def list_user_pending_tasks(session: Session, user_id: str, include_discarded: bool = False) -> List[Task]:
    statement = select(Task).where(
        Task.user_id == user_id,
        Task.completion_status.in_([CompletionStatusEnum.PENDING, CompletionStatusEnum.IN_PROGRESS]),
    )
    if not include_discarded:
        statement = statement.where(Task.completion_status != CompletionStatusEnum.DISCARDED)
    return session.exec(statement).all()


def complete_task(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise LookupError("Task not found")
    
    # Set completion status with timezone-aware datetime
    task.completion_status = CompletionStatusEnum.COMPLETED
    task.completed_at = datetime.now().replace(tzinfo=timezone.utc).astimezone()
    
    # Update the updated_at timestamp using system default timezone
    task.updated_at = datetime.now().replace(tzinfo=timezone.utc).astimezone()
    
    # Calculate actual duration if started_at exists
    if task.started_at and not task.actual_duration:
        # Handle timezone-aware vs timezone-naive datetime comparison
        started_at = task.started_at
        if started_at.tzinfo is None:
            # If started_at is timezone-naive, assume it's in UTC (common for stored timestamps)
            # and convert to system timezone for comparison
            started_at = started_at.replace(tzinfo=timezone.utc).astimezone()
        elif started_at.tzinfo != task.completed_at.tzinfo:
            # If it has a different timezone, convert to system timezone
            started_at = started_at.astimezone()
        
        duration = task.completed_at - started_at
        task.actual_duration = int(duration.total_seconds() / 60)  # Convert to minutes
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


