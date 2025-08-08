from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import model_validator


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


class TaskBase(BaseModel):
    description: str
    deadline: Optional[datetime] = None
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    completion_status: CompletionStatusEnum = CompletionStatusEnum.PENDING
    estimated_duration: Optional[int] = Field(default=None, ge=0)  # minutes
    actual_duration: Optional[int] = Field(default=None, ge=0)     # minutes
    energy_required: EnergyRequiredEnum = EnergyRequiredEnum.MEDIUM
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_timestamps(self) -> "TaskBase":
        if self.created_at and self.updated_at and self.created_at > self.updated_at:
            raise ValueError("created_at cannot be after updated_at")
        return self


class TaskCreate(TaskBase):
    user_id: Optional[str] = None
    goal_id: Optional[int] = None


class TaskResponse(TaskBase):
    task_id: int
    goal_id: Optional[int] = None
    ai_generated: bool = False
    user_id: str

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    goal_id: Optional[int] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[TaskPriorityEnum] = None
    ai_generated: Optional[bool] = None
    completion_status: Optional[CompletionStatusEnum] = None
    estimated_duration: Optional[int] = Field(default=None, ge=0)
    actual_duration: Optional[int] = Field(default=None, ge=0)
    energy_required: Optional[EnergyRequiredEnum] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_update_timestamps(self) -> "TaskUpdate":
        if self.started_at and self.completed_at and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot be before started_at")
        if self.created_at and self.updated_at and self.created_at > self.updated_at:
            raise ValueError("created_at cannot be after updated_at")
        return self


class TaskUpdate2(BaseModel):
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[TaskPriorityEnum] = None
    completion_status: Optional[CompletionStatusEnum] = None
    estimated_duration: Optional[int] = Field(default=None, ge=0)
    actual_duration: Optional[int] = Field(default=None, ge=0)
    energy_required: Optional[EnergyRequiredEnum] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BulkTaskCreate(BaseModel):
    tasks: list[TaskCreate] = Field(..., min_items=1, max_items=100)  # Limit to 100 tasks per request