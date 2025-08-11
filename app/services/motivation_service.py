from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlmodel import Session, select

from app.models.user import User
from app.models.ai_context import AIContext
from app.models.task import Task, CompletionStatusEnum
from app.services.ai_service import AIService
from app.services.ai_context_service import get_ai_context_by_user
from app.services.task_service import list_tasks


async def generate_motivation(
    session: Session,
    user_id: str,
    current_challenge: str = "",
    stress_level: int = 5
) -> Dict[str, Any]:
    """
    Generate personalized motivation for a user based on their context and current situation.
    
    Args:
        session: Database session
        user_id: User's telegram ID
        current_challenge: User's current challenge or situation
        stress_level: User's stress level (1-10)
    
    Returns:
        Dictionary containing motivation data
    """
    try:
        # Get user
        user = session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get AI context for the user
        try:
            ai_context = get_ai_context_by_user(session, user_id)
        except LookupError:
            # Create default AI context if none exists
            from app.schemas.ai_context import AIContextCreate
            from app.services.ai_context_service import create_ai_context
            
            ai_context_data = AIContextCreate(
                user_id=user_id,
                motivation_triggers="Achievement, Progress, Recognition"
            )
            ai_context = await create_ai_context(session, ai_context_data)
        
        # Get recent completed tasks (last 7 days)
        recent_completions = list_tasks(
            session=session,
            user_id=user_id,
            completion_status=CompletionStatusEnum.COMPLETED,
            limit=10
        )
        
        # Filter to last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        recent_completions = [
            task for task in recent_completions 
            if task.updated_at and task.updated_at >= week_ago
        ]
        
        # Initialize AI service
        ai_service = AIService()
        
        # Generate motivation message
        motivation_text = await ai_service.generate_motivation_message(
            user=user,
            ai_context=ai_context,
            current_challenge=current_challenge,
            stress_level=stress_level,
            recent_completions=recent_completions
        )
        
        # Get additional context for response
        pending_tasks = list_tasks(
            session=session,
            user_id=user_id,
            completion_status=CompletionStatusEnum.PENDING,
            limit=5
        )
        
        # Calculate completion rate for this week
        total_week_tasks = len(recent_completions) + len(pending_tasks)
        completion_rate = (len(recent_completions) / max(total_week_tasks, 1)) * 100
        
        return {
            "motivation_text": motivation_text,
            "current_challenge": current_challenge,
            "stress_level": stress_level,
            "recent_achievements": len(recent_completions),
            "pending_tasks": len(pending_tasks),
            "completion_rate": round(completion_rate, 1),
            "user_phase": user.current_phase,
            "days_until_target": (user.quit_job_target - date.today()).days if user.quit_job_target else None
        }
        
    except Exception as e:
        # Fallback motivation
        return {
            "motivation_text": f"You're making progress on your entrepreneurial journey! Every challenge you face is building the resilience you'll need to successfully transition from your job. Keep focusing on your goals - you're closer than you think!",
            "current_challenge": current_challenge,
            "stress_level": stress_level,
            "recent_achievements": 0,
            "pending_tasks": 0,
            "completion_rate": 0,
            "user_phase": "Unknown",
            "days_until_target": None,
            "error": str(e)
        }


def get_motivation_stats(session: Session, user_id: str) -> Dict[str, Any]:
    """
    Get motivation-related statistics for a user.
    
    Args:
        session: Database session
        user_id: User's telegram ID
    
    Returns:
        Dictionary containing motivation statistics
    """
    try:
        # Get user
        user = session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get tasks for the last 30 days
        month_ago = datetime.now() - timedelta(days=30)
        
        all_tasks = list_tasks(
            session=session,
            user_id=user_id,
            limit=100
        )
        
        # Filter to last 30 days
        recent_tasks = [
            task for task in all_tasks 
            if task.created_at and task.created_at >= month_ago
        ]
        
        completed_tasks = [t for t in recent_tasks if t.completion_status == CompletionStatusEnum.COMPLETED]
        pending_tasks = [t for t in recent_tasks if t.completion_status == CompletionStatusEnum.PENDING]
        
        # Calculate statistics
        total_tasks = len(recent_tasks)
        completion_rate = (len(completed_tasks) / max(total_tasks, 1)) * 100
        
        # Get streak information
        streak_days = 0
        current_date = date.today()
        
        for i in range(30):
            check_date = current_date - timedelta(days=i)
            day_tasks = [t for t in completed_tasks if t.updated_at and t.updated_at.date() == check_date]
            if day_tasks:
                streak_days += 1
            else:
                break
        
        return {
            "total_tasks_30_days": total_tasks,
            "completed_tasks_30_days": len(completed_tasks),
            "pending_tasks": len(pending_tasks),
            "completion_rate_30_days": round(completion_rate, 1),
            "current_streak_days": streak_days,
            "user_phase": user.current_phase,
            "days_until_target": (user.quit_job_target - current_date).days if user.quit_job_target else None
        }
        
    except Exception as e:
        return {
            "total_tasks_30_days": 0,
            "completed_tasks_30_days": 0,
            "pending_tasks": 0,
            "completion_rate_30_days": 0,
            "current_streak_days": 0,
            "user_phase": "Unknown",
            "days_until_target": None,
            "error": str(e)
        }
