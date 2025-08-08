from datetime import datetime
from sqlmodel import SQLModel, Field

class TimestampModel(SQLModel):
    """Base model class that automatically includes created_at and updated_at fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

from .user import User
from .goal import Goal
from .task import Task
from .progress_log import ProgressLog
from .ai_context import AIContext
from .job_metrics import JobMetrics
from .day_log import DayLog

__all__ = [
    "TimestampModel",
    "User",
    "Goal",
    "Task",
    "ProgressLog",
    "AIContext",
    "JobMetrics",
    "DayLog"
]