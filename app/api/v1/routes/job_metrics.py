from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.core.database import get_session
from app.models.job_metrics import JobMetrics
from app.schemas.job_metrics import JobMetricsCreate, JobMetricsUpdate, JobMetricsResponse
from app.models.user import User
from app.services.job_metrics_service import analyze_job_metrics_with_ai, AIServiceError

router = APIRouter()

@router.post("/", response_model=JobMetricsResponse, status_code=status.HTTP_201_CREATED)
def create_job_metrics(job_metrics: JobMetricsCreate, session: Session = Depends(get_session)):
    """Create job metrics for a user."""
    # Verify user exists
    user = session.get(User, job_metrics.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if job metrics already exist for this user
    existing_metrics = session.exec(
        select(JobMetrics).where(JobMetrics.user_id == job_metrics.user_id)
    ).first()
    
    if existing_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job metrics already exist for this user"
        )
    
    # Calculate quit readiness score if we have enough data
    db_job_metrics = JobMetrics.model_validate(job_metrics)
    if db_job_metrics.startup_revenue and db_job_metrics.current_salary and db_job_metrics.monthly_expenses:
        db_job_metrics.quit_readiness_score = _calculate_quit_readiness_score(db_job_metrics)
    
    session.add(db_job_metrics)
    session.commit()
    session.refresh(db_job_metrics)
    return db_job_metrics

@router.get("/", response_model=List[JobMetricsResponse])
def read_job_metrics(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get all job metrics with optional user filtering."""
    statement = select(JobMetrics)
    if user_id:
        statement = statement.where(JobMetrics.user_id == user_id)
    statement = statement.offset(skip).limit(limit)
    job_metrics = session.exec(statement).all()
    return job_metrics

@router.get("/{metric_id}", response_model=JobMetricsResponse)
def read_job_metric(metric_id: int, session: Session = Depends(get_session)):
    """Get a specific job metric by ID."""
    job_metric = session.get(JobMetrics, metric_id)
    if not job_metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job metrics not found"
        )
    return job_metric

@router.put("/{metric_id}", response_model=JobMetricsResponse)
def update_job_metrics(metric_id: int, job_metrics_update: JobMetricsUpdate, session: Session = Depends(get_session)):
    """Update job metrics."""
    job_metrics = session.get(JobMetrics, metric_id)
    if not job_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job metrics not found"
        )
    
    job_metrics_data = job_metrics_update.model_dump(exclude_unset=True)
    for field, value in job_metrics_data.items():
        setattr(job_metrics, field, value)
    
    # Recalculate quit readiness score if financial data changed
    if any(field in job_metrics_data for field in ['startup_revenue', 'current_salary', 'monthly_expenses']):
        if job_metrics.startup_revenue and job_metrics.current_salary and job_metrics.monthly_expenses:
            job_metrics.quit_readiness_score = _calculate_quit_readiness_score(job_metrics)
    
    job_metrics.last_updated = datetime.utcnow()
    session.add(job_metrics)
    session.commit()
    session.refresh(job_metrics)
    return job_metrics

@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_metrics(metric_id: int, session: Session = Depends(get_session)):
    """Delete job metrics."""
    job_metrics = session.get(JobMetrics, metric_id)
    if not job_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job metrics not found"
        )
    
    session.delete(job_metrics)
    session.commit()
    return None

@router.get("/user/{user_id}", response_model=JobMetricsResponse)
def get_user_job_metrics(user_id: str, session: Session = Depends(get_session)):
    """Get job metrics for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    job_metrics = session.exec(
        select(JobMetrics).where(JobMetrics.user_id == user_id)
    ).first()
    
    if not job_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job metrics not found for this user"
        )
    
    return job_metrics

@router.patch("/user/{user_id}/financial", response_model=JobMetricsResponse)
def update_financial_metrics(
    user_id: str, 
    financial_data: dict,
    session: Session = Depends(get_session)
):
    """Update financial metrics for a user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    job_metrics = session.exec(
        select(JobMetrics).where(JobMetrics.user_id == user_id)
    ).first()
    
    if not job_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job metrics not found for this user"
        )
    
    # Update financial fields
    valid_fields = ['current_salary', 'startup_revenue', 'monthly_expenses']
    for field, value in financial_data.items():
        if field in valid_fields:
            setattr(job_metrics, field, Decimal(str(value)) if value else None)
    
    # Recalculate derived metrics
    if job_metrics.startup_revenue and job_metrics.current_salary and job_metrics.monthly_expenses:
        job_metrics.quit_readiness_score = _calculate_quit_readiness_score(job_metrics)
        job_metrics.runway_months = float(job_metrics.startup_revenue / job_metrics.monthly_expenses) if job_metrics.monthly_expenses > 0 else None
    
    job_metrics.last_updated = datetime.utcnow()
    session.add(job_metrics)
    session.commit()
    session.refresh(job_metrics)
    return job_metrics

@router.get("/user/{user_id}/analysis", response_model=dict)
def get_financial_analysis(user_id: str, session: Session = Depends(get_session)):
    """Get financial analysis and recommendations for a user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    job_metrics = session.exec(
        select(JobMetrics).where(JobMetrics.user_id == user_id)
    ).first()
    
    if not job_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job metrics not found for this user"
        )
    
    analysis = {
        "financial_health": "Unknown",
        "runway_months": job_metrics.runway_months,
        "quit_readiness_score": job_metrics.quit_readiness_score,
        "recommendations": [],
        "risk_level": "Unknown"
    }
    
    if job_metrics.startup_revenue and job_metrics.current_salary and job_metrics.monthly_expenses:
        monthly_salary = job_metrics.current_salary / 12
        revenue_ratio = float(job_metrics.startup_revenue / monthly_salary)
        
        if revenue_ratio >= 1.0:
            analysis["financial_health"] = "Excellent"
            analysis["risk_level"] = "Low"
            analysis["recommendations"].append("You're financially ready to make the transition")
        elif revenue_ratio >= 0.5:
            analysis["financial_health"] = "Good"
            analysis["risk_level"] = "Medium"
            analysis["recommendations"].append("Consider building more revenue before transitioning")
        else:
            analysis["financial_health"] = "Needs Improvement"
            analysis["risk_level"] = "High"
            analysis["recommendations"].append("Focus on increasing startup revenue significantly")
        
        if job_metrics.runway_months and job_metrics.runway_months < 6:
            analysis["recommendations"].append("Build at least 6 months of runway before quitting")
        
        if job_metrics.stress_level >= 8:
            analysis["recommendations"].append("High stress levels detected - consider transition timeline")
        
        if job_metrics.job_satisfaction <= 3:
            analysis["recommendations"].append("Low job satisfaction - factor in quality of life improvements")
    
    return analysis

@router.post("/{metric_id}/analyze", response_model=JobMetricsResponse)
async def analyze_metrics_with_ai(metric_id: int, session: Session = Depends(get_session)):
    """
    Analyze job metrics using AI to provide comprehensive insights and recommendations.
    """
    try:
        job_metrics = await analyze_job_metrics_with_ai(session, metric_id)
        return job_metrics
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing job metrics: {str(e)}"
        )

def _calculate_quit_readiness_score(job_metrics: JobMetrics) -> float:
    """Calculate a quit readiness score based on financial and personal metrics."""
    if not all([job_metrics.startup_revenue, job_metrics.current_salary, job_metrics.monthly_expenses]):
        return 0.0
    
    # Financial readiness (40% weight)
    monthly_salary = job_metrics.current_salary / 12
    revenue_ratio = min(float(job_metrics.startup_revenue / monthly_salary), 2.0)  # Cap at 200%
    financial_score = (revenue_ratio / 2.0) * 40
    
    # Runway score (30% weight)
    runway_score = 0
    if job_metrics.runway_months:
        runway_score = min(job_metrics.runway_months / 12, 1.0) * 30  # Cap at 12 months
    
    # Personal readiness (30% weight)
    stress_factor = (10 - job_metrics.stress_level) / 10  # Lower stress = higher readiness
    satisfaction_factor = job_metrics.job_satisfaction / 10  # Higher satisfaction = lower readiness (paradox)
    personal_score = ((stress_factor + (1 - satisfaction_factor)) / 2) * 30
    
    total_score = financial_score + runway_score + personal_score
    return round(min(total_score, 100.0), 2) 