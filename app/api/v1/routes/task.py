from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, date
from app.core.database import get_session
from app.models.task import Task
from app.models.user import User
from app.models.goal import Goal
from app.schemas import task as schemas
from app.schemas.task import CompletionStatusEnum, BulkTaskCreate, TaskCreate, TaskUpdate

router = APIRouter()

@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session)
):
    """Create a new task."""
    # Verify user exists
    user = session.get(User, task.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate goal belongs to user if provided
    if task.goal_id is not None:
        goal = session.get(Goal, task.goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if goal.user_id != task.user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goal does not belong to user")

    db_task = Task(
        user_id=task.user_id,
        goal_id=task.goal_id,
        description=task.description,
        deadline=task.deadline,
        priority=task.priority,
        ai_generated=bool(getattr(task, 'ai_generated', False)),
        completion_status=task.completion_status,
        estimated_duration=task.estimated_duration,
        actual_duration=task.actual_duration,
        energy_required=task.energy_required
    )
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@router.get("/", response_model=List[schemas.TaskResponse])
def read_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: Optional[str] = None,
    goal_id: Optional[int] = None,
    completion_status: Optional[CompletionStatusEnum] = None,
    session: Session = Depends(get_session)
):
    """Get all tasks with optional filtering."""
    statement = select(Task)
    if user_id:
        statement = statement.where(Task.user_id == user_id)
    
    if goal_id:
        statement = statement.where(Task.goal_id == goal_id)
    if completion_status:
        statement = statement.where(Task.completion_status == completion_status)
    
    statement = statement.offset(skip).limit(limit)
    tasks = session.exec(statement).all()
    return tasks


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def read_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific task by ID."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
):
    """Update a task."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task_data = task_update.model_dump(exclude_unset=True)
    
    # Validate duration fields
    if task_data.get("estimated_duration") is not None and task_data["estimated_duration"] < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Estimated duration cannot be negative"
        )
    if task_data.get("actual_duration") is not None and task_data["actual_duration"] < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Actual duration cannot be negative"
        )
    
    # Validate goal existence if goal_id is provided
    if task_data.get("goal_id") is not None:
        goal = session.get(Goal, task_data["goal_id"])
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        # Verify goal belongs to the task's user
        if goal.user_id != task.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Goal does not belong to the task's user"
            )
    
    for field, value in task_data.items():
        setattr(task, field, value)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """Delete a task."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    session.delete(task)
    session.commit()
    return None


@router.get("/user/{user_id}/pending", response_model=List[schemas.TaskResponse])
def get_user_pending_tasks(
    user_id: str,
    session: Session = Depends(get_session)
):
    """Get all pending tasks for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    statement = select(Task).where(
        Task.user_id == user_id,
        Task.completion_status.in_([CompletionStatusEnum.PENDING, CompletionStatusEnum.IN_PROGRESS])
    )
    tasks = session.exec(statement).all()
    return tasks


@router.get("/user/{user_id}", response_model=List[schemas.TaskResponse])
def get_user_tasks(
    user_id: str,
    session: Session = Depends(get_session)
):
    """Get all tasks for a specific user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    statement = select(Task).where(Task.user_id == user_id)
    return session.exec(statement).all()

@router.get("/user/{user_id}/today", response_model=List[schemas.TaskResponse])
def get_user_today_tasks(
    user_id: str,
    session: Session = Depends(get_session)
):
    """Get all tasks due today for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    today = date.today()
    statement = select(Task).where(
        Task.user_id == user_id,
        Task.deadline >= datetime.combine(today, datetime.min.time()),
        Task.deadline < datetime.combine(today, datetime.max.time())
    )
    tasks = session.exec(statement).all()
    return tasks


@router.patch("/{task_id}/complete", response_model=schemas.TaskResponse)
def complete_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """Mark a task as completed."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task.completion_status = CompletionStatusEnum.COMPLETED
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.post("/bulk", response_model=List[schemas.TaskResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_tasks(
    bulk_tasks: BulkTaskCreate,
    session: Session = Depends(get_session)
):
    """Create multiple tasks in a single request."""
    created_tasks = []
    try:
        # Create all tasks
        for task_data in bulk_tasks.tasks:
            # Verify user exists for each task
            user = session.get(User, task_data.user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            db_task = Task(
                user_id=task_data.user_id,
                description=task_data.description,
                deadline=task_data.deadline,
                priority=task_data.priority,
                ai_generated=False,
                completion_status=task_data.completion_status,
                estimated_duration=task_data.estimated_duration,
                actual_duration=task_data.actual_duration,
                energy_required=task_data.energy_required,
            )
            session.add(db_task)
            created_tasks.append(db_task)
        
        session.commit()
        
        # Refresh all tasks to get their IDs
        for task in created_tasks:
            session.refresh(task)
        
        return created_tasks
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )