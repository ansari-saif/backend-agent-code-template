from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class ProgressLogBase(BaseModel):
    user_id: str
    date: date
    tasks_completed: int = 0
    tasks_planned: int = 0
    mood_score: int = Field(ge=1, le=10)
    energy_level: int = Field(ge=1, le=10)
    focus_score: int = Field(ge=1, le=10)
    daily_reflection: Optional[str] = None
    ai_insights: Optional[str] = None


class ProgressLogCreate(ProgressLogBase):
    pass


class ProgressLogResponse(ProgressLogBase):
    log_id: int

    class Config:
        from_attributes = True


class ProgressLogUpdate(BaseModel):
    date: Optional[date] = None
    tasks_completed: Optional[int] = None
    tasks_planned: Optional[int] = None
    mood_score: Optional[int] = Field(default=None, ge=1, le=10)
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    focus_score: Optional[int] = Field(default=None, ge=1, le=10)
    daily_reflection: Optional[str] = None
    ai_insights: Optional[str] = None
