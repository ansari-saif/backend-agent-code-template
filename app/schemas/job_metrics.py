from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class JobMetricsAIAnalysis(BaseModel):
    career_growth_score: float
    financial_health_score: float
    work_life_balance_score: float
    overall_recommendation: str
    action_items: list[str]
    risk_factors: list[str]
    opportunities: list[str]

class JobMetricsBase(BaseModel):
    user_id: str
    current_salary: Decimal
    startup_revenue: Decimal
    monthly_expenses: Decimal
    runway_months: float
    stress_level: int
    job_satisfaction: int
    quit_readiness_score: float
    ai_analysis: Optional[JobMetricsAIAnalysis] = None


class JobMetricsCreate(JobMetricsBase):
    pass


class JobMetricsResponse(JobMetricsBase):
    last_updated: datetime

    class Config:
        from_attributes = True


class JobMetricsUpdate(BaseModel):
    current_salary: Optional[Decimal] = None
    startup_revenue: Optional[Decimal] = None
    monthly_expenses: Optional[Decimal] = None
    runway_months: Optional[float] = None
    stress_level: Optional[int] = None
    job_satisfaction: Optional[int] = None
    quit_readiness_score: Optional[float] = None
