from typing import List, Optional
from datetime import date, datetime
from sqlmodel import Session, select

from app.models.task import Task
from app.models.goal import Goal
from app.schemas.task import TaskCreate, TaskUpdate, CompletionStatusEnum


def create_task(session: Session, data: TaskCreate) -> Task:
    task = Task(
        user_id=data.user_id,
        goal_id=data.goal_id,
        description=data.description,
        deadline=data.deadline,
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
) -> List[Task]:
    statement = select(Task)
    if user_id:
        statement = statement.where(Task.user_id == user_id)
    if goal_id:
        statement = statement.where(Task.goal_id == goal_id)
    if completion_status:
        statement = statement.where(Task.completion_status == completion_status)
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
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: int) -> None:
    task = session.get(Task, task_id)
    if not task:
        raise LookupError("Task not found")
    session.delete(task)
    session.commit()


def list_user_tasks(session: Session, user_id: str) -> List[Task]:
    return session.exec(select(Task).where(Task.user_id == user_id)).all()


def list_user_today_tasks(session: Session, user_id: str) -> List[Task]:
    today = date.today()
    return session.exec(
        select(Task).where(
            Task.user_id == user_id,
            Task.deadline >= datetime.combine(today, datetime.min.time()),
            Task.deadline < datetime.combine(today, datetime.max.time()),
        )
    ).all()


def list_user_pending_tasks(session: Session, user_id: str) -> List[Task]:
    return session.exec(
        select(Task).where(
            Task.user_id == user_id,
            Task.completion_status.in_([CompletionStatusEnum.PENDING, CompletionStatusEnum.IN_PROGRESS]),
        )
    ).all()


def complete_task(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise LookupError("Task not found")
    task.completion_status = CompletionStatusEnum.COMPLETED
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


