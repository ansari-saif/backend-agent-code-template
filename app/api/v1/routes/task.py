from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, date
from app.core.database import get_session
from app.models.task import Task, TaskCreate, TaskUpdate
from app.models.user import User
from app.models.goal import Goal

router = APIRouter()

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    """Create a new task."""
    # Verify user exists
    user = session.get(User, task.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify goal exists if provided
    if task.goal_id:
        goal = session.get(Goal, task.goal_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        # Verify goal belongs to user
        if goal.user_id != task.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Goal does not belong to the specified user"
            )
    
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.get("/", response_model=List[Task])
def read_tasks(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[str] = None,
    goal_id: Optional[int] = None,
    completion_status: Optional[str] = None,
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

@router.get("/{task_id}", response_model=Task)
def read_task(task_id: int, session: Session = Depends(get_session)):
    """Get a specific task by ID."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.put("/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate, session: Session = Depends(get_session)):
    """Update a task."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task_data = task_update.model_dump(exclude_unset=True)
    for field, value in task_data.items():
        setattr(task, field, value)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, session: Session = Depends(get_session)):
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

@router.get("/user/{user_id}", response_model=List[Task])
def get_user_tasks(user_id: str, session: Session = Depends(get_session)):
    """Get all tasks for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    statement = select(Task).where(Task.user_id == user_id)
    tasks = session.exec(statement).all()
    return tasks

@router.get("/user/{user_id}/pending", response_model=List[Task])
def get_user_pending_tasks(user_id: str, session: Session = Depends(get_session)):
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
        Task.completion_status.in_(["Not Started", "In Progress"])
    )
    tasks = session.exec(statement).all()
    return tasks

@router.get("/user/{user_id}/today", response_model=List[Task])
def get_user_today_tasks(user_id: str, session: Session = Depends(get_session)):
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

@router.patch("/{task_id}/complete", response_model=Task)
def complete_task(task_id: int, session: Session = Depends(get_session)):
    """Mark a task as completed."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task.completion_status = "Completed"
    session.add(task)
    session.commit()
    session.refresh(task)
    return task 