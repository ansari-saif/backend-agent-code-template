from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.core.database import get_session
from app.models.progress_log import ProgressLog, ProgressLogCreate, ProgressLogUpdate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ProgressLog, status_code=status.HTTP_201_CREATED)
def create_progress_log(progress_log: ProgressLogCreate, session: Session = Depends(get_session)):
    """Create a new progress log entry."""
    # Verify user exists
    user = session.get(User, progress_log.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if log already exists for this user and date
    existing_log = session.exec(
        select(ProgressLog).where(
            ProgressLog.user_id == progress_log.user_id,
            ProgressLog.date == progress_log.date
        )
    ).first()
    
    if existing_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress log already exists for this date"
        )
    
    db_progress_log = ProgressLog.model_validate(progress_log)
    session.add(db_progress_log)
    session.commit()
    session.refresh(db_progress_log)
    return db_progress_log

@router.get("/", response_model=List[ProgressLog])
def read_progress_logs(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """Get all progress logs with optional filtering."""
    statement = select(ProgressLog)
    
    if user_id:
        statement = statement.where(ProgressLog.user_id == user_id)
    if start_date:
        statement = statement.where(ProgressLog.date >= start_date)
    if end_date:
        statement = statement.where(ProgressLog.date <= end_date)
    
    statement = statement.order_by(ProgressLog.date.desc()).offset(skip).limit(limit)
    progress_logs = session.exec(statement).all()
    return progress_logs

@router.get("/{log_id}", response_model=ProgressLog)
def read_progress_log(log_id: int, session: Session = Depends(get_session)):
    """Get a specific progress log by ID."""
    progress_log = session.get(ProgressLog, log_id)
    if not progress_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress log not found"
        )
    return progress_log

@router.put("/{log_id}", response_model=ProgressLog)
def update_progress_log(log_id: int, progress_log_update: ProgressLogUpdate, session: Session = Depends(get_session)):
    """Update a progress log."""
    progress_log = session.get(ProgressLog, log_id)
    if not progress_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress log not found"
        )
    
    progress_log_data = progress_log_update.model_dump(exclude_unset=True)
    for field, value in progress_log_data.items():
        setattr(progress_log, field, value)
    
    session.add(progress_log)
    session.commit()
    session.refresh(progress_log)
    return progress_log

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress_log(log_id: int, session: Session = Depends(get_session)):
    """Delete a progress log."""
    progress_log = session.get(ProgressLog, log_id)
    if not progress_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress log not found"
        )
    
    session.delete(progress_log)
    session.commit()
    return None

@router.get("/user/{user_id}", response_model=List[ProgressLog])
def get_user_progress_logs(user_id: str, session: Session = Depends(get_session)):
    """Get all progress logs for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    statement = select(ProgressLog).where(
        ProgressLog.user_id == user_id
    ).order_by(ProgressLog.date.desc())
    progress_logs = session.exec(statement).all()
    return progress_logs

@router.get("/user/{user_id}/recent", response_model=List[ProgressLog])
def get_user_recent_progress_logs(user_id: str, days: int = 7, session: Session = Depends(get_session)):
    """Get recent progress logs for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    start_date = date.today() - timedelta(days=days)
    statement = select(ProgressLog).where(
        ProgressLog.user_id == user_id,
        ProgressLog.date >= start_date
    ).order_by(ProgressLog.date.desc())
    progress_logs = session.exec(statement).all()
    return progress_logs

@router.get("/user/{user_id}/stats", response_model=dict)
def get_user_progress_stats(user_id: str, days: int = 30, session: Session = Depends(get_session)):
    """Get progress statistics for a user over a specified period."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    start_date = date.today() - timedelta(days=days)
    statement = select(ProgressLog).where(
        ProgressLog.user_id == user_id,
        ProgressLog.date >= start_date
    )
    progress_logs = session.exec(statement).all()
    
    if not progress_logs:
        return {
            "period_days": days,
            "total_entries": 0,
            "avg_tasks_completed": 0,
            "avg_tasks_planned": 0,
            "avg_mood_score": 0,
            "avg_energy_level": 0,
            "avg_focus_score": 0,
            "completion_rate": 0
        }
    
    total_entries = len(progress_logs)
    total_completed = sum(log.tasks_completed for log in progress_logs)
    total_planned = sum(log.tasks_planned for log in progress_logs)
    total_mood = sum(log.mood_score for log in progress_logs)
    total_energy = sum(log.energy_level for log in progress_logs)
    total_focus = sum(log.focus_score for log in progress_logs)
    
    return {
        "period_days": days,
        "total_entries": total_entries,
        "avg_tasks_completed": round(total_completed / total_entries, 2),
        "avg_tasks_planned": round(total_planned / total_entries, 2),
        "avg_mood_score": round(total_mood / total_entries, 2),
        "avg_energy_level": round(total_energy / total_entries, 2),
        "avg_focus_score": round(total_focus / total_entries, 2),
        "completion_rate": round((total_completed / max(total_planned, 1)) * 100, 2)
    } 