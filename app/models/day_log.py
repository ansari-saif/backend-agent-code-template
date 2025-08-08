from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date, datetime


class DayLogBase(SQLModel):
    user_id: str = Field(foreign_key="users.telegram_id")
    date: date
    start_time: datetime
    end_time: Optional[datetime] = None
    summary: Optional[str] = None
    highlights: Optional[str] = None
    challenges: Optional[str] = None
    learnings: Optional[str] = None
    gratitude: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    weather: Optional[str] = None
    location: Optional[str] = None


class DayLogCreate(DayLogBase):
    pass


class DayLog(DayLogBase, table=True):
    __tablename__ = "day_logs"
    
    log_id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="day_logs")


class DayLogUpdate(SQLModel):
    date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    summary: Optional[str] = None
    highlights: Optional[str] = None
    challenges: Optional[str] = None
    learnings: Optional[str] = None
    gratitude: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    weather: Optional[str] = None
    location: Optional[str] = None
