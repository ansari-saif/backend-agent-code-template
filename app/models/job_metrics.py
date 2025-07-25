from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal


class JobMetricsBase(SQLModel):
    user_id: str = Field(foreign_key="users.telegram_id")
    current_salary: Optional[Decimal] = None
    startup_revenue: Optional[Decimal] = None
    monthly_expenses: Optional[Decimal] = None
    runway_months: Optional[float] = None
    stress_level: int = Field(ge=1, le=10)
    job_satisfaction: int = Field(ge=1, le=10)
    quit_readiness_score: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class JobMetricsCreate(JobMetricsBase):
    pass


class JobMetrics(JobMetricsBase, table=True):
    __tablename__ = "job_metrics"
    
    metric_id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="job_metrics")


class JobMetricsUpdate(SQLModel):
    current_salary: Optional[Decimal] = None
    startup_revenue: Optional[Decimal] = None
    monthly_expenses: Optional[Decimal] = None
    runway_months: Optional[float] = None
    stress_level: Optional[int] = Field(default=None, ge=1, le=10)
    job_satisfaction: Optional[int] = Field(default=None, ge=1, le=10)
    quit_readiness_score: Optional[float] = None
    last_updated: Optional[datetime] = Field(default_factory=datetime.utcnow) 