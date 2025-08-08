from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import JSON, Column
from app.models import TimestampModel

if TYPE_CHECKING:
    from app.models.user import User


class JobMetricsAIAnalysis(SQLModel):
    career_growth_score: Optional[float] = Field(default=None)
    financial_health_score: Optional[float] = Field(default=None)
    work_life_balance_score: Optional[float] = Field(default=None)
    overall_recommendation: Optional[str] = Field(default=None)
    action_items: List[str] = Field(sa_column=Column(JSON), default_factory=list)
    risk_factors: List[str] = Field(sa_column=Column(JSON), default_factory=list)
    opportunities: List[str] = Field(sa_column=Column(JSON), default_factory=list)

class JobMetricsBase(TimestampModel):
    user_id: str = Field(foreign_key="users.telegram_id")
    current_salary: Optional[Decimal] = None
    startup_revenue: Optional[Decimal] = None
    monthly_expenses: Optional[Decimal] = None
    runway_months: Optional[float] = None
    stress_level: int = Field(ge=1, le=10)
    job_satisfaction: int = Field(ge=1, le=10)
    quit_readiness_score: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # AI Analysis fields
    ai_analysis: Optional[dict] = Field(sa_column=Column(JSON), default=None)


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