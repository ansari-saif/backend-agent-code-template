from typing import List, Optional
from datetime import date, timedelta
from sqlmodel import Session, select

from app.models.progress_log import ProgressLog
from app.schemas.progress_log import ProgressLogCreate, ProgressLogUpdate


def create_progress_log(session: Session, data: ProgressLogCreate) -> ProgressLog:
    existing_log = session.exec(
        select(ProgressLog).where(
            ProgressLog.user_id == data.user_id,
            ProgressLog.date == data.date,
        )
    ).first()
    if existing_log:
        raise ValueError("Progress log already exists for this date")

    log = ProgressLog.model_validate(data)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def list_progress_logs(
    session: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[ProgressLog]:
    statement = select(ProgressLog)
    if user_id:
        statement = statement.where(ProgressLog.user_id == user_id)
    if start_date:
        statement = statement.where(ProgressLog.date >= start_date)
    if end_date:
        statement = statement.where(ProgressLog.date <= end_date)
    statement = statement.order_by(ProgressLog.date.desc()).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_progress_log(session: Session, log_id: int) -> Optional[ProgressLog]:
    return session.get(ProgressLog, log_id)


def update_progress_log(session: Session, log_id: int, update: ProgressLogUpdate) -> ProgressLog:
    log = session.get(ProgressLog, log_id)
    if not log:
        raise LookupError("Progress log not found")
    data = update.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(log, field, value)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def delete_progress_log(session: Session, log_id: int) -> None:
    log = session.get(ProgressLog, log_id)
    if not log:
        raise LookupError("Progress log not found")
    session.delete(log)
    session.commit()


def list_user_progress_logs(session: Session, user_id: str) -> List[ProgressLog]:
    statement = select(ProgressLog).where(ProgressLog.user_id == user_id).order_by(ProgressLog.date.desc())
    return session.exec(statement).all()


def list_user_recent_progress_logs(session: Session, user_id: str, days: int = 7) -> List[ProgressLog]:
    start_date = date.today() - timedelta(days=days)
    statement = select(ProgressLog).where(
        ProgressLog.user_id == user_id,
        ProgressLog.date >= start_date,
    ).order_by(ProgressLog.date.desc())
    return session.exec(statement).all()


def user_progress_stats(session: Session, user_id: str, days: int = 30) -> dict:
    start_date = date.today() - timedelta(days=days)
    statement = select(ProgressLog).where(
        ProgressLog.user_id == user_id,
        ProgressLog.date >= start_date,
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
            "completion_rate": 0,
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
        "completion_rate": round((total_completed / max(total_planned, 1)) * 100, 2),
    }


