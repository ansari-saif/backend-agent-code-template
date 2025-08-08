from sqlmodel import Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import date, time
from sqlalchemy import Column, String, Enum as SAEnum
from app.schemas.user import TimezoneEnum, PhaseEnum, EnergyProfileEnum
from app.models import TimestampModel

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.task import Task
    from app.models.progress_log import ProgressLog
    from app.models.ai_context import AIContext
    from app.models.job_metrics import JobMetrics
    from app.models.day_log import DayLog
    # from app.models.todo import Todo


class User(TimestampModel, table=True):
    __tablename__ = "users"
    
    # Core fields
    telegram_id: str = Field(primary_key=True)
    name: str
    birthday: Optional[date] = None
    timezone: TimezoneEnum = Field(
        default=TimezoneEnum.UTC,
        sa_column=Column(String, nullable=False)
    )
    current_phase: PhaseEnum = Field(
        default=PhaseEnum.RESEARCH,
        sa_column=Column(SAEnum(PhaseEnum, name="phaseenum_user", create_type=False), nullable=False)
    )
    quit_job_target: Optional[date] = None
    onboarding_complete: bool = Field(default=False)
    morning_time: Optional[time] = None
    energy_profile: EnergyProfileEnum = Field(
        default=EnergyProfileEnum.MORNING,
        sa_column=Column(String, nullable=False)
    )
    
    # Relationships
    goals: List["Goal"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    progress_logs: List["ProgressLog"] = Relationship(back_populates="user")
    ai_context: Optional["AIContext"] = Relationship(back_populates="user")
    job_metrics: Optional["JobMetrics"] = Relationship(back_populates="user")
    day_logs: List["DayLog"] = Relationship(back_populates="user")
    # todos relationship removed (Todo module deprecated)