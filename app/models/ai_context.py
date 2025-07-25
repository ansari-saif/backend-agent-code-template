from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime


class AIContextBase(SQLModel):
    user_id: str = Field(foreign_key="users.telegram_id")
    behavior_patterns: Optional[str] = None  # JSON string
    productivity_insights: Optional[str] = None
    motivation_triggers: Optional[str] = None
    stress_indicators: Optional[str] = None
    optimal_work_times: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AIContextCreate(AIContextBase):
    pass


class AIContext(AIContextBase, table=True):
    __tablename__ = "ai_contexts"
    
    context_id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="ai_context")


class AIContextUpdate(SQLModel):
    behavior_patterns: Optional[str] = None
    productivity_insights: Optional[str] = None
    motivation_triggers: Optional[str] = None
    stress_indicators: Optional[str] = None
    optimal_work_times: Optional[str] = None
    last_updated: Optional[datetime] = Field(default_factory=datetime.utcnow) 