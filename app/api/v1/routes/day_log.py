from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from typing import List
from datetime import date, datetime, timedelta

from app.core.database import get_session
from app.services.day_log_service import create_day_log, create_bulk_day_logs
from app.services.ai_service import AIService
from app.models.day_log import DayLog
from app.models.user import User
from app.schemas.day_log import DayLogCreate, DayLogResponse, DayLogUpdate, DayLogBulkCreate

router = APIRouter()
ai_service = AIService()


@router.post("/", response_model=DayLogResponse, status_code=status.HTTP_201_CREATED)
def create_day_log_endpoint(
    day_log: DayLogCreate,
    session: Session = Depends(get_session)
):
    """Create a new day log entry."""
    # Verify user exists
    user = session.get(User, day_log.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate end_time is after start_time if provided
    if day_log.end_time and day_log.end_time < day_log.start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="End time must be after start time"
        )

    db_day_log = DayLog.model_validate(day_log)
    session.add(db_day_log)
    session.commit()
    session.refresh(db_day_log)
    return db_day_log


@router.get("/{log_id}", response_model=DayLogResponse)
def get_day_log(
    log_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific day log entry by ID."""

    day_log = session.get(DayLog, log_id)
    if not day_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day log not found"
        )
    return day_log


@router.get("/user/{user_id}", response_model=List[DayLogResponse])
def get_user_day_logs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    location: str = None,
    weather: str = None,
    session: Session = Depends(get_session)
):
    """Get all day logs for a specific user with optional filtering."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    query = select(DayLog).where(DayLog.user_id == user_id)

    if location:
        query = query.where(DayLog.location == location)
    if weather:
        query = query.where(DayLog.weather == weather)

    query = query.offset(skip).limit(limit)
    day_logs = session.exec(query).all()
    return day_logs


@router.get("/user/{user_id}/date/{date}", response_model=DayLogResponse)
def get_user_day_log_by_date(
    user_id: str,
    date: date,
    session: Session = Depends(get_session)
):
    """Get a user's day log for a specific date."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    day_log = session.exec(
        select(DayLog)
        .where(DayLog.user_id == user_id, DayLog.date == date)
    ).first()
    if not day_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day log not found"
        )
    return day_log


@router.get("/user/{user_id}/range", response_model=List[DayLogResponse])
def get_user_day_logs_by_date_range(
    user_id: str,
    start_date: date,
    end_date: date,
    location: str = None,
    session: Session = Depends(get_session)
):
    """Get user's day logs within a date range."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="End date must be after start date"
        )

    query = select(DayLog).where(
        DayLog.user_id == user_id,
        DayLog.date >= start_date,
        DayLog.date <= end_date
    )

    if location:
        query = query.where(DayLog.location == location)

    day_logs = session.exec(query).all()
    return day_logs


@router.get("/user/{user_id}/stats")
def get_user_day_log_stats(
    user_id: str,
    session: Session = Depends(get_session)
):
    """Get statistics about user's day logs."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    day_logs = session.exec(
        select(DayLog).where(DayLog.user_id == user_id)
    ).all()

    if not day_logs:
        return {
            "total_logs": 0,
            "average_duration": 0,
            "locations_summary": {},
            "weather_summary": {}
        }

    # Calculate statistics
    total_duration = 0
    locations = {}
    weather = {}
    count_with_duration = 0

    for log in day_logs:
        if log.end_time and log.start_time:
            duration = (log.end_time - log.start_time).total_seconds() / 3600  # hours
            total_duration += duration
            count_with_duration += 1

        if log.location:
            locations[log.location] = locations.get(log.location, 0) + 1
        if log.weather:
            weather[log.weather] = weather.get(log.weather, 0) + 1

    return {
        "total_logs": len(day_logs),
        "average_duration": total_duration / count_with_duration if count_with_duration > 0 else 0,
        "locations_summary": locations,
        "weather_summary": weather
    }


@router.patch("/{log_id}", response_model=DayLogResponse)
def update_day_log_endpoint(
    log_id: int,
    day_log_update: DayLogUpdate,
    session: Session = Depends(get_session)
):
    """Update a day log entry."""
    db_day_log = session.get(DayLog, log_id)
    if not db_day_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day log not found"
        )

    update_data = day_log_update.model_dump(exclude_unset=True)

    # Validate end_time if provided
    if "end_time" in update_data and update_data["end_time"]:
        start_time = update_data.get("start_time", db_day_log.start_time)
        if update_data["end_time"] < start_time:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End time must be after start time"
            )

    for key, value in update_data.items():
        setattr(db_day_log, key, value)

    session.add(db_day_log)
    session.commit()
    session.refresh(db_day_log)
    return db_day_log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_day_log_endpoint(
    log_id: int,
    session: Session = Depends(get_session)
):
    """Delete a day log entry."""
    day_log = session.get(DayLog, log_id)
    if not day_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day log not found"
        )

    session.delete(day_log)
    session.commit()
    return None


@router.post("/bulk", response_model=List[DayLogResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_day_logs_endpoint(
    bulk_data: DayLogBulkCreate,
    session: Session = Depends(get_session)
):
    """Create multiple day log entries for a user."""
    # Verify user exists
    user = session.get(User, bulk_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate end_time is after start_time for each log if provided
    for log in bulk_data.day_logs:
        if log.end_time and log.end_time < log.start_time:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End time must be after start time"
            )

    try:
        db_logs = create_bulk_day_logs(session, bulk_data.user_id, bulk_data.day_logs)
        return db_logs
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/generate/{user_id}", response_model=DayLogResponse, status_code=status.HTTP_201_CREATED)
async def generate_day_log(
    user_id: str,
    date_value: date | None = None,
    session: Session = Depends(get_session)
):
    """
    Generate a DayLog using AI for the given user and optional date (defaults to today).
    Fills the narrative fields (summary, highlights, challenges, learnings, gratitude, tomorrow_plan).
    """
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    target_date = date_value or datetime.utcnow().date()

    # If an entry already exists for that date, return 400
    existing = session.exec(
        select(DayLog).where(DayLog.user_id == user_id, DayLog.date == target_date)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Day log already exists for this date")

    # Ask AI for content
    content = await ai_service.generate_day_log_content(session=session, user_id=user_id, target_date=target_date)

    now = datetime.utcnow()
    db_log = DayLog(
        user_id=user_id,
        date=target_date,
        start_time=now,
        summary=content.get("summary"),
        highlights=content.get("highlights"),
        challenges=content.get("challenges"),
        learnings=content.get("learnings"),
        gratitude=content.get("gratitude"),
        tomorrow_plan=content.get("tomorrow_plan"),
        created_at=now,
        updated_at=now,
    )

    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log