from sqlmodel import Session, select
from datetime import datetime
import json
from typing import List, Optional

from app.models.ai_context import AIContext
from app.models.user import User
from app.models.goal import Goal
from app.models.task import Task
from app.models.job_metrics import JobMetrics
from app.models.progress_log import ProgressLog
from app.schemas.ai_context import AIContextCreate, AIContextUpdate
from app.services.ai_service import AIService


async def create_ai_context(session: Session, ai_context_data: AIContextCreate) -> AIContext:
    """Create a new AI context.

    Behavior:
    - If payload includes any explicit context fields, store as-is (no user check, no AI generation).
    - Otherwise, auto-generate insights using AI for an existing user (requires user to exist).
    """

    has_explicit_fields = any(
        getattr(ai_context_data, field) is not None
        for field in [
            "behavior_patterns",
            "productivity_insights",
            "motivation_triggers",
            "stress_indicators",
            "optimal_work_times",
        ]
    )

    if has_explicit_fields:
        # Direct create without AI; match integration tests expecting echo of input
        ai_context = AIContext(
            user_id=ai_context_data.user_id,
            behavior_patterns=ai_context_data.behavior_patterns,
            productivity_insights=ai_context_data.productivity_insights,
            motivation_triggers=ai_context_data.motivation_triggers,
            stress_indicators=ai_context_data.stress_indicators,
            optimal_work_times=ai_context_data.optimal_work_times,
        )
        session.add(ai_context)
        session.commit()
        session.refresh(ai_context)
        return ai_context

    # Auto-generation path requires a valid user
    user = session.get(User, ai_context_data.user_id)
    if not user:
        raise ValueError(f"User {ai_context_data.user_id} not found")

    # Get user's goals
    goals = session.exec(select(Goal).where(Goal.user_id == user.telegram_id)).all()
    # Get user's tasks
    tasks = session.exec(select(Task).where(Task.user_id == user.telegram_id)).all()
    # Get user's job metrics
    job_metrics = session.exec(select(JobMetrics).where(JobMetrics.user_id == user.telegram_id)).first()
    # Get user's progress logs (last 30 days)
    progress_logs = session.exec(
        select(ProgressLog)
        .where(ProgressLog.user_id == user.telegram_id)
        .order_by(ProgressLog.created_at.desc())
        .limit(30)
    ).all()

    # Initialize AI service
    ai_service = AIService()

    # Generate insights using AI
    goals_analysis = await ai_service.analyze_goals(goals, progress_logs)
    career_analysis = (
        await ai_service.analyze_career_transition_readiness(user, job_metrics)
        if job_metrics
        else None
    )

    # Determine behavior patterns
    behavior_patterns = {
        "productivity_style": "focused" if user.energy_profile == "Morning" else "flexible",
        "peak_hours": ["09:00-12:00"] if user.energy_profile == "Morning" else ["14:00-17:00"],
        "work_consistency": "high" if progress_logs and len(progress_logs) >= 5 else "medium",
        "task_completion_rate": sum(
            1 for t in tasks if getattr(t.completion_status, "value", str(t.completion_status)) in ["Completed", "CompletionStatusEnum.COMPLETED"]
        )
        / max(len(tasks), 1)
        * 100,
    }

    # Generate productivity insights
    productivity_insights = {
        "overall_status": goals_analysis.get("overall_status"),
        "key_insights": goals_analysis.get("key_insights"),
        "success_patterns": goals_analysis.get("success_patterns"),
        "focus_areas": goals_analysis.get("focus_areas"),
    }

    # Generate motivation triggers
    motivation_triggers = {
        "strengths": (career_analysis.get("key_strengths") if career_analysis else ["Goal-oriented", "Consistent tracking"]),
        "achievement_patterns": goals_analysis.get("success_patterns"),
        "response_to_challenges": "resilient" if goals_analysis.get("achievement_score", 0) > 70 else "developing",
    }

    # Generate stress indicators
    stress_indicators = {
        "risk_level": (career_analysis.get("risk_level") if career_analysis else "Medium"),
        "current_stressors": (career_analysis.get("concerns") if career_analysis else ["Work-life balance"]),
        "coping_mechanisms": ["Regular progress tracking", "Clear goal setting"],
    }

    # Determine optimal work times based on energy profile and progress logs
    if user.energy_profile == "Morning":
        optimal_work_times = ["09:00-12:00", "14:00-16:00"]
    elif user.energy_profile == "Afternoon":
        optimal_work_times = ["11:00-13:00", "15:00-18:00"]
    else:
        optimal_work_times = ["10:00-12:00", "14:00-17:00"]

    # Create AI context with generated insights
    ai_context = AIContext(
        user_id=user.telegram_id,
        behavior_patterns=json.dumps(behavior_patterns),
        productivity_insights=json.dumps(productivity_insights),
        motivation_triggers=json.dumps(motivation_triggers),
        stress_indicators=json.dumps(stress_indicators),
        optimal_work_times=json.dumps(optimal_work_times),
    )

    session.add(ai_context)
    session.commit()
    session.refresh(ai_context)
    return ai_context


def get_ai_context(session: Session, context_id: int) -> AIContext:
    """Get an AI context by its ID."""
    ai_context = session.get(AIContext, context_id)
    if not ai_context:
        raise LookupError(f"AIContext with ID {context_id} not found")
    return ai_context


def get_ai_context_by_user(session: Session, user_id: str) -> AIContext:
    """Get an AI context by user ID."""
    statement = select(AIContext).where(AIContext.user_id == user_id)
    ai_context = session.exec(statement).first()
    if not ai_context:
        raise LookupError(f"AIContext for user {user_id} not found")
    return ai_context


def update_ai_context(
    session: Session, context_id: int, ai_context_data: AIContextUpdate
) -> AIContext:
    """Update an existing AI context."""
    ai_context = get_ai_context(session, context_id)
    
    update_data = ai_context_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ai_context, key, value)
    
    ai_context.last_updated = datetime.utcnow()
    session.add(ai_context)
    session.commit()
    session.refresh(ai_context)
    return ai_context


def delete_ai_context(session: Session, context_id: int) -> None:
    """Delete an AI context."""
    ai_context = get_ai_context(session, context_id)
    session.delete(ai_context)
    session.commit()