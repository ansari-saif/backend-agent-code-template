from sqlmodel import Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import date as dt_date
from app.models import TimestampModel

if TYPE_CHECKING:
    from app.models.user import User


class ProgressLog(TimestampModel, table=True):
    __tablename__ = "progress_logs"
    
    log_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.telegram_id")
    date: dt_date = Field(default_factory=dt_date.today)
    tasks_completed: int = 0
    tasks_planned: int = 0
    mood_score: int = Field(ge=1, le=10)
    energy_level: int = Field(ge=1, le=10)
    focus_score: int = Field(ge=1, le=10)
    daily_reflection: Optional[str] = None
    ai_insights: Optional[str] = None
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="progress_logs")