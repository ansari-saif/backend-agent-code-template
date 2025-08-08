from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date


class ProgressLog(SQLModel, table=True):
    __tablename__ = "progress_logs"
    
    log_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.telegram_id")
    date: date
    tasks_completed: int = 0
    tasks_planned: int = 0
    mood_score: int = Field(ge=1, le=10)
    energy_level: int = Field(ge=1, le=10)
    focus_score: int = Field(ge=1, le=10)
    daily_reflection: Optional[str] = None
    ai_insights: Optional[str] = None
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="progress_logs")