from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from app.core.database import get_session
from app.services.ai_service import AIService
from app.models.user import User, PhaseEnum
from app.models.goal import Goal, StatusEnum, GoalTypeEnum
from app.models.task import Task, CompletionStatusEnum
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext
from app.models.job_metrics import JobMetrics
from pydantic import BaseModel, Field

router = APIRouter()

# Request models
class DailyTasksRequest(BaseModel):
    user_id: str
    energy_level: int = Field(default=5, ge=1, le=10)
    current_phase: Optional[PhaseEnum] = None

class MotivationRequest(BaseModel):
    user_id: str
    current_challenge: str
    stress_level: int = 5

class DeadlineReminderRequest(BaseModel):
    task_id: int
    user_pattern: str = "default"

class WeeklyAnalysisRequest(BaseModel):
    user_id: str
    weeks: int = 1

class PhaseTransitionRequest(BaseModel):
    user_id: str
    current_phase: str = None

class CareerTransitionRequest(BaseModel):
    user_id: str

# Initialize AI service
ai_service = AIService()

@router.post("/daily-tasks", response_model=List[Dict[str, Any]])
async def generate_daily_tasks(request: DailyTasksRequest, session: Session = Depends(get_session)):
    """Generate AI-powered daily tasks for a user."""
    # Verify user exists
    user = session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get recent progress logs (last 7 days)
        start_date = date.today() - timedelta(days=7)
        recent_progress = session.exec(
            select(ProgressLog).where(
                ProgressLog.user_id == request.user_id,
                ProgressLog.date >= start_date
            ).order_by(ProgressLog.date.desc())
        ).all()
        
        # Get pending goals
        pending_goals = session.exec(
            select(Goal).where(
                Goal.user_id == request.user_id,
                Goal.status == StatusEnum.ACTIVE,
                Goal.phase == (request.current_phase or user.current_phase)
            )
        ).all()
        
        # Generate daily tasks using AI
        tasks = await ai_service.generate_daily_tasks(
            user=user,
            recent_progress=recent_progress,
            pending_goals=pending_goals,
            today_energy_level=request.energy_level
        )
        
        return tasks
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily tasks: {str(e)}"
        )

@router.post("/motivation", response_model=str)
async def generate_motivation(request: MotivationRequest, session: Session = Depends(get_session)):
    """Generate AI-powered motivation message for a user."""
    # Verify user exists
    user = session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get AI context
        ai_context = session.exec(
            select(AIContext).where(AIContext.user_id == request.user_id)
        ).first()
        
        if not ai_context:
            # Create default AI context if none exists
            ai_context = AIContext(
                user_id=request.user_id,
                behavior_patterns="{}",
                motivation_triggers="Achievement, Progress, Recognition"
            )
        
        # Get recent completed tasks (last 7 days)
        start_date = date.today() - timedelta(days=7)
        recent_completions = session.exec(
            select(Task).where(
                Task.user_id == request.user_id,
                Task.completion_status == "Completed"
            )
        ).all()
        
        # Generate motivation message using AI
        motivation = await ai_service.generate_motivation_message(
            user=user,
            ai_context=ai_context,
            current_challenge=request.current_challenge,
            stress_level=request.stress_level,
            recent_completions=recent_completions
        )
        
        return motivation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate motivation: {str(e)}"
        )

@router.post("/deadline-reminder", response_model=str)
async def generate_deadline_reminder(request: DeadlineReminderRequest, session: Session = Depends(get_session)):
    """Generate AI-powered deadline reminder for a task."""
    # Get task
    task = session.get(Task, request.task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    try:
        # Calculate time remaining
        if task.deadline:
            time_remaining = str(task.deadline - task.created_at if hasattr(task, 'created_at') else "Unknown")
        else:
            time_remaining = "No deadline set"
        
        # Get user's completion rate
        user_tasks = session.exec(
            select(Task).where(Task.user_id == task.user_id)
        ).all()
        
        completed_tasks = [t for t in user_tasks if t.completion_status == "Completed"]
        completion_rate = len(completed_tasks) / len(user_tasks) if user_tasks else 0.0
        
        # Get user's stress level from recent progress
        recent_progress = session.exec(
            select(ProgressLog).where(
                ProgressLog.user_id == task.user_id
            ).order_by(ProgressLog.date.desc()).limit(1)
        ).first()
        
        stress_level = recent_progress.mood_score if recent_progress else 5
        
        # Generate deadline reminder using AI
        reminder = await ai_service.generate_deadline_reminder(
            task=task,
            time_remaining=time_remaining,
            user_pattern=request.user_pattern,
            stress_level=stress_level,
            completion_rate=completion_rate
        )
        
        return reminder
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate deadline reminder: {str(e)}"
        )

@router.post("/weekly-analysis", response_model=Dict[str, Any])
async def generate_weekly_analysis(request: WeeklyAnalysisRequest, session: Session = Depends(get_session)):
    """Generate AI-powered weekly analysis for a user."""
    # Verify user exists
    user = session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get progress logs for the specified weeks
        start_date = date.today() - timedelta(weeks=request.weeks)
        progress_logs = session.exec(
            select(ProgressLog).where(
                ProgressLog.user_id == request.user_id,
                ProgressLog.date >= start_date
            ).order_by(ProgressLog.date.desc())
        ).all()
        
        # Get goals for the period
        goals = session.exec(
            select(Goal).where(Goal.user_id == request.user_id)
        ).all()
        
        # Get tasks for the period
        tasks = session.exec(
            select(Task).where(Task.user_id == request.user_id)
        ).all()
        
        # Generate weekly analysis using AI
        analysis = await ai_service.generate_weekly_analysis(
            progress_logs=progress_logs,
            goals=goals,
            tasks=tasks
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weekly analysis: {str(e)}"
        )

@router.post("/phase-transition", response_model=Dict[str, Any])
async def evaluate_phase_transition(request: PhaseTransitionRequest, session: Session = Depends(get_session)):
    """Evaluate phase transition readiness for a user."""
    # Verify user exists
    user = session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get user goals
        goals = session.exec(
            select(Goal).where(Goal.user_id == request.user_id)
        ).all()
        
        # Calculate time in current phase (simplified - assuming user creation date)
        # In a real app, you'd track phase transition dates
        time_in_phase_days = 30  # Default placeholder
        
        # Generate phase transition evaluation using AI
        evaluation = await ai_service.evaluate_phase_transition(
            user=user,
            goals=goals,
            time_in_phase_days=time_in_phase_days
        )
        
        return evaluation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate phase transition: {str(e)}"
        )

@router.post("/career-transition", response_model=Dict[str, Any])
async def analyze_career_transition(request: CareerTransitionRequest, session: Session = Depends(get_session)):
    """Analyze career transition readiness for a user."""
    # Verify user exists
    user = session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get job metrics
        job_metrics = session.exec(
            select(JobMetrics).where(JobMetrics.user_id == request.user_id)
        ).first()
        
        if not job_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job metrics not found for this user"
            )
        
        # Generate career transition analysis using AI
        analysis = await ai_service.analyze_career_transition_readiness(
            user=user,
            job_metrics=job_metrics
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze career transition: {str(e)}"
        )

@router.get("/health")
def ai_service_health():
    """Health check for AI service."""
    return {"status": "healthy", "service": "AI Service", "version": "1.0.0"}

@router.post("/user/{user_id}/complete-analysis", response_model=Dict[str, Any])
async def generate_complete_user_analysis(user_id: str, session: Session = Depends(get_session)):
    """Generate a complete AI analysis for a user combining all agents."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Gather all user data
        recent_progress = session.exec(
            select(ProgressLog).where(
                ProgressLog.user_id == user_id,
                ProgressLog.date >= date.today() - timedelta(days=7)
            )
        ).all()
        
        goals = session.exec(
            select(Goal).where(Goal.user_id == user_id)
        ).all()
        
        tasks = session.exec(
            select(Task).where(Task.user_id == user_id)
        ).all()
        
        ai_context = session.exec(
            select(AIContext).where(AIContext.user_id == user_id)
        ).first()
        
        job_metrics = session.exec(
            select(JobMetrics).where(JobMetrics.user_id == user_id)
        ).first()
        
        # Generate comprehensive analysis
        analysis = {
            "user_id": user_id,
            "analysis_date": date.today().isoformat(),
            "summary": "Complete AI-powered user analysis"
        }
        
        # Add individual agent outputs if data is available
        if recent_progress and goals:
            daily_tasks = await ai_service.generate_daily_tasks(
                user=user,
                recent_progress=recent_progress,
                pending_goals=[g for g in goals if g.status == StatusEnum.ACTIVE],
                today_energy_level=7
            )
            analysis["recommended_daily_tasks"] = daily_tasks
        
        if ai_context:
            motivation = await ai_service.generate_motivation_message(
                user=user,
                ai_context=ai_context,
                current_challenge="Daily productivity optimization",
                stress_level=5,
                recent_completions=[t for t in tasks if t.completion_status == CompletionStatusEnum.COMPLETED]
            )
            analysis["motivation_message"] = motivation
        
        if recent_progress and goals and tasks:
            weekly_analysis = await ai_service.generate_weekly_analysis(
                progress_logs=recent_progress,
                goals=goals,
                tasks=tasks
            )
            analysis["weekly_insights"] = weekly_analysis
        
        phase_evaluation = await ai_service.evaluate_phase_transition(
            user=user,
            goals=goals,
            time_in_phase_days=30
        )
        analysis["phase_transition_readiness"] = phase_evaluation
        
        if job_metrics:
            career_analysis = await ai_service.analyze_career_transition_readiness(
                user=user,
                job_metrics=job_metrics
            )
            analysis["career_transition_analysis"] = career_analysis
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate complete analysis: {str(e)}"
        ) 