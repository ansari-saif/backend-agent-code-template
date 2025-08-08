from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AIContextBase(BaseModel):
    user_id: str
    behavior_patterns: Optional[str] = None
    productivity_insights: Optional[str] = None
    motivation_triggers: Optional[str] = None
    stress_indicators: Optional[str] = None
    optimal_work_times: Optional[str] = None


class AIContextCreate(AIContextBase):
    pass


class AIContextResponse(AIContextBase):
    context_id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class AIContextUpdate(BaseModel):
    behavior_patterns: Optional[str] = None
    productivity_insights: Optional[str] = None
    motivation_triggers: Optional[str] = None
    stress_indicators: Optional[str] = None
    optimal_work_times: Optional[str] = None
