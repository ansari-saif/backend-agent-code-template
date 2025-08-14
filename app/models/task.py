from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, date, time
from sqlalchemy import Column, String, Enum
from app.schemas.task import TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models import TimestampModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.goal import Goal


class Task(TimestampModel, table=True):
    __tablename__ = "tasks"
    
    task_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.telegram_id")
    goal_id: Optional[int] = Field(default=None, foreign_key="goals.goal_id")
    description: str
    priority: TaskPriorityEnum = Field(
        default=TaskPriorityEnum.MEDIUM,
        sa_column=Column(Enum(TaskPriorityEnum, name='taskpriorityenum', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    )
    ai_generated: bool = Field(default=False)
    completion_status: CompletionStatusEnum = Field(
        default=CompletionStatusEnum.PENDING,
        sa_column=Column(Enum(CompletionStatusEnum, name='completionstatusenum', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    )
    estimated_duration: Optional[int] = Field(default=None, ge=0)  # minutes
    actual_duration: Optional[int] = Field(default=None, ge=0)     # minutes
    energy_required: EnergyRequiredEnum = Field(
        default=EnergyRequiredEnum.MEDIUM,
        sa_column=Column(Enum(EnergyRequiredEnum, name='energyrequiredenum', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    )
    scheduled_for_date: Optional[date] = Field(default=None)
    scheduled_for_time: Optional[time] = Field(default=None)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    discard_message: Optional[str] = None
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="tasks")
    goal: Optional["Goal"] = Relationship(back_populates="tasks")