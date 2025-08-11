from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Dict, Any

from app.core.database import get_session
from app.services.motivation_service import generate_motivation, get_motivation_stats
from app.schemas.motivation import MotivationRequest, MotivationResponse, MotivationStatsResponse


router = APIRouter()


@router.post("/generate", response_model=MotivationResponse)
async def generate_motivation_endpoint(
    request: MotivationRequest,
    session: Session = Depends(get_session)
):
    """
    Generate personalized motivation for a user.
    
    This endpoint uses AI to generate contextual motivation based on:
    - User's current phase and goals
    - Recent task completions
    - Current challenges and stress level
    - AI context and motivation triggers
    """
    try:
        motivation_data = await generate_motivation(
            session=session,
            user_id=request.user_id,
            current_challenge=request.current_challenge,
            stress_level=request.stress_level
        )
        
        return MotivationResponse(
            user_id=request.user_id,
            motivation_text=motivation_data["motivation_text"],
            current_challenge=motivation_data["current_challenge"],
            stress_level=motivation_data["stress_level"],
            recent_achievements=motivation_data["recent_achievements"],
            pending_tasks=motivation_data["pending_tasks"],
            completion_rate=motivation_data["completion_rate"],
            user_phase=motivation_data["user_phase"],
            days_until_target=motivation_data["days_until_target"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate motivation: {str(e)}")


@router.get("/stats/{user_id}", response_model=MotivationStatsResponse)
async def get_motivation_stats_endpoint(
    user_id: str,
    session: Session = Depends(get_session)
):
    """
    Get motivation-related statistics for a user.
    
    Returns:
    - Task completion rates
    - Current streak information
    - Progress towards goals
    - User phase information
    """
    try:
        stats = get_motivation_stats(session=session, user_id=user_id)
        
        return MotivationStatsResponse(
            user_id=user_id,
            total_tasks_30_days=stats["total_tasks_30_days"],
            completed_tasks_30_days=stats["completed_tasks_30_days"],
            pending_tasks=stats["pending_tasks"],
            completion_rate_30_days=stats["completion_rate_30_days"],
            current_streak_days=stats["current_streak_days"],
            user_phase=stats["user_phase"],
            days_until_target=stats["days_until_target"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get motivation stats: {str(e)}")
