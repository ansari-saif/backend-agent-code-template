from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, date
from app.core.database import get_session
from app.models.task import Task
from app.models.user import User
from app.models.goal import Goal
from app.schemas import task as schemas
from app.schemas.task import CompletionStatusEnum, BulkTaskCreate, TaskCreate, TaskUpdate, TaskDiscard, TaskRestore
from app.services import task_service

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

    try:
        db_task = task_service.create_task(session, task)
        return db_task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[schemas.TaskResponse])
def read_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: Optional[str] = None,
    goal_id: Optional[int] = None,
    completion_status: Optional[CompletionStatusEnum] = None,
    include_discarded: bool = Query(False, description="Include discarded tasks in results"),
    session: Session = Depends(get_session)
):
    """Get all tasks with optional filtering."""
    try:
        tasks = task_service.list_tasks(
            session=session,
            skip=skip,
            limit=limit,
            user_id=user_id,
            goal_id=goal_id,
            completion_status=completion_status,
            include_discarded=include_discarded
        )
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/discarded", response_model=List[schemas.TaskResponse])
def list_discarded_tasks(
    user_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """Get all discarded tasks."""
    try:
        tasks = task_service.list_discarded_tasks(
            session=session,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def read_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific task by ID."""
    task = task_service.get_task(session, task_id)
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
    try:
        task = task_service.update_task(session, task_id, task_update)
        return task
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{task_id}/discard", response_model=schemas.TaskResponse)
def discard_task(
    task_id: int,
    discard_data: TaskDiscard,
    session: Session = Depends(get_session)
):
    """Discard a task with a message explaining why it was discarded."""
    try:
        task = task_service.discard_task(session, task_id, discard_data)
        return task
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{task_id}/restore", response_model=schemas.TaskResponse)
def restore_task(
    task_id: int,
    restore_data: Optional[TaskRestore] = None,
    session: Session = Depends(get_session)
):
    """Restore a discarded task back to pending status."""
    try:
        task = task_service.restore_task(session, task_id, restore_data)
        return task
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """Delete a task permanently."""
    try:
        task_service.delete_task(session, task_id)
        return None
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.get("/user/{user_id}/pending", response_model=List[schemas.TaskResponse])
def get_user_pending_tasks(
    user_id: str,
    include_discarded: bool = Query(False, description="Include discarded tasks in results"),
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
    
    try:
        tasks = task_service.list_user_pending_tasks(session, user_id, include_discarded)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/user/{user_id}", response_model=List[schemas.TaskResponse])
def get_user_tasks(
    user_id: str,
    include_discarded: bool = Query(False, description="Include discarded tasks in results"),
    session: Session = Depends(get_session)
):
    """Get all tasks for a specific user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        tasks = task_service.list_user_tasks(session, user_id, include_discarded)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/user/{user_id}/today", response_model=List[schemas.TaskResponse])
def get_user_today_tasks(
    user_id: str,
    include_discarded: bool = Query(False, description="Include discarded tasks in results"),
    session: Session = Depends(get_session)
):
    """Get today's tasks for a specific user based on scheduled_for_date only."""
    from datetime import date
    
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        tasks = task_service.list_user_today_tasks(session, user_id, include_discarded)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{task_id}/complete", response_model=schemas.TaskResponse)
def complete_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """Mark a task as completed."""
    try:
        task = task_service.complete_task(session, task_id)
        return task
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


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
                priority=task_data.priority,
                ai_generated=False,
                completion_status=task_data.completion_status,
                estimated_duration=task_data.estimated_duration,
                actual_duration=task_data.actual_duration,
                energy_required=task_data.energy_required,
                scheduled_for_date=task_data.scheduled_for_date,
                scheduled_for_time=getattr(task_data, "scheduled_for_time", None),
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