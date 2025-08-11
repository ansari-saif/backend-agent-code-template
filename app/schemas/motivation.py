from pydantic import BaseModel, Field
from typing import Optional


class MotivationRequest(BaseModel):
    """Request schema for motivation generation."""
    user_id: str = Field(..., description="User's telegram ID")
    current_challenge: str = Field(default="", description="User's current challenge or situation")
    stress_level: int = Field(default=5, ge=1, le=10, description="User's stress level (1-10)")


class MotivationResponse(BaseModel):
    """Response schema for motivation generation."""
    user_id: str = Field(..., description="User's telegram ID")
    motivation_text: str = Field(..., description="AI-generated motivation message")
    current_challenge: str = Field(..., description="User's current challenge")
    stress_level: int = Field(..., description="User's stress level")
    recent_achievements: int = Field(..., description="Number of recent task completions")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    completion_rate: float = Field(..., description="Task completion rate percentage")
    user_phase: str = Field(..., description="User's current entrepreneurial phase")
    days_until_target: Optional[int] = Field(None, description="Days until job transition target")
    
    class Config:
        from_attributes = True


class MotivationStatsResponse(BaseModel):
    """Response schema for motivation statistics."""
    user_id: str = Field(..., description="User's telegram ID")
    total_tasks_30_days: int = Field(..., description="Total tasks created in last 30 days")
    completed_tasks_30_days: int = Field(..., description="Tasks completed in last 30 days")
    pending_tasks: int = Field(..., description="Current pending tasks")
    completion_rate_30_days: float = Field(..., description="30-day task completion rate percentage")
    current_streak_days: int = Field(..., description="Current streak of days with completed tasks")
    user_phase: str = Field(..., description="User's current entrepreneurial phase")
    days_until_target: Optional[int] = Field(None, description="Days until job transition target")
    
    class Config:
        from_attributes = True
