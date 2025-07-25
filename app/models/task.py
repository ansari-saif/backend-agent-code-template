from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskPriorityEnum(str, Enum):
    URGENT = "Urgent"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CompletionStatusEnum(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class EnergyRequiredEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskBase(SQLModel):
    user_id: str = Field(foreign_key="users.telegram_id")
    goal_id: Optional[int] = Field(default=None, foreign_key="goals.goal_id")
    description: str
    deadline: Optional[datetime] = None
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    ai_generated: bool = False
    completion_status: CompletionStatusEnum = CompletionStatusEnum.PENDING
    estimated_duration: Optional[int] = None  # minutes
    actual_duration: Optional[int] = None     # minutes
    energy_required: EnergyRequiredEnum = EnergyRequiredEnum.MEDIUM


class TaskCreate(TaskBase):
    pass


class Task(TaskBase, table=True):
    __tablename__ = "tasks"
    
    task_id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="tasks")
    goal: Optional["Goal"] = Relationship(back_populates="tasks")


class TaskUpdate(SQLModel):
    goal_id: Optional[int] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[TaskPriorityEnum] = None
    ai_generated: Optional[bool] = None
    completion_status: Optional[CompletionStatusEnum] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    energy_required: Optional[EnergyRequiredEnum] = None 