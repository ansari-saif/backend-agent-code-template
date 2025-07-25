from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Optional
import json
from datetime import datetime
from app.core.database import get_session
from app.models.ai_context import AIContext, AIContextCreate, AIContextUpdate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=AIContext, status_code=status.HTTP_201_CREATED)
def create_ai_context(ai_context: AIContextCreate, session: Session = Depends(get_session)):
    """Create AI context for a user."""
    # Verify user exists
    user = session.get(User, ai_context.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if AI context already exists for this user
    existing_context = session.exec(
        select(AIContext).where(AIContext.user_id == ai_context.user_id)
    ).first()
    
    if existing_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI context already exists for this user"
        )
    
    # Validate JSON fields if provided
    if ai_context.behavior_patterns:
        try:
            json.loads(ai_context.behavior_patterns)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format in behavior_patterns"
            )
    
    db_ai_context = AIContext.model_validate(ai_context)
    session.add(db_ai_context)
    session.commit()
    session.refresh(db_ai_context)
    return db_ai_context

@router.get("/", response_model=List[AIContext])
def read_ai_contexts(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get all AI contexts with optional user filtering."""
    statement = select(AIContext)
    if user_id:
        statement = statement.where(AIContext.user_id == user_id)
    statement = statement.offset(skip).limit(limit)
    ai_contexts = session.exec(statement).all()
    return ai_contexts

@router.get("/{context_id}", response_model=AIContext)
def read_ai_context(context_id: int, session: Session = Depends(get_session)):
    """Get a specific AI context by ID."""
    ai_context = session.get(AIContext, context_id)
    if not ai_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI context not found"
        )
    return ai_context

@router.put("/{context_id}", response_model=AIContext)
def update_ai_context(context_id: int, ai_context_update: AIContextUpdate, session: Session = Depends(get_session)):
    """Update an AI context."""
    ai_context = session.get(AIContext, context_id)
    if not ai_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI context not found"
        )
    
    # Validate JSON fields if provided
    update_data = ai_context_update.model_dump(exclude_unset=True)
    if "behavior_patterns" in update_data and update_data["behavior_patterns"]:
        try:
            json.loads(update_data["behavior_patterns"])
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format in behavior_patterns"
            )
    
    for field, value in update_data.items():
        setattr(ai_context, field, value)
    
    ai_context.last_updated = datetime.utcnow()
    session.add(ai_context)
    session.commit()
    session.refresh(ai_context)
    return ai_context

@router.delete("/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_context(context_id: int, session: Session = Depends(get_session)):
    """Delete an AI context."""
    ai_context = session.get(AIContext, context_id)
    if not ai_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI context not found"
        )
    
    session.delete(ai_context)
    session.commit()
    return None

@router.get("/user/{user_id}", response_model=AIContext)
def get_user_ai_context(user_id: str, session: Session = Depends(get_session)):
    """Get AI context for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    ai_context = session.exec(
        select(AIContext).where(AIContext.user_id == user_id)
    ).first()
    
    if not ai_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI context not found for this user"
        )
    
    return ai_context

@router.patch("/user/{user_id}/patterns", response_model=AIContext)
def update_behavior_patterns(user_id: str, patterns: dict, session: Session = Depends(get_session)):
    """Update behavior patterns for a user's AI context."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    ai_context = session.exec(
        select(AIContext).where(AIContext.user_id == user_id)
    ).first()
    
    if not ai_context:
        # Create new AI context if it doesn't exist
        ai_context_data = AIContextCreate(
            user_id=user_id,
            behavior_patterns=json.dumps(patterns)
        )
        ai_context = AIContext.model_validate(ai_context_data)
        session.add(ai_context)
    else:
        # Update existing patterns
        ai_context.behavior_patterns = json.dumps(patterns)
        ai_context.last_updated = datetime.utcnow()
        session.add(ai_context)
    
    session.commit()
    session.refresh(ai_context)
    return ai_context

@router.patch("/user/{user_id}/insights", response_model=AIContext)
def update_productivity_insights(user_id: str, insights: str, session: Session = Depends(get_session)):
    """Update productivity insights for a user's AI context."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    ai_context = session.exec(
        select(AIContext).where(AIContext.user_id == user_id)
    ).first()
    
    if not ai_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI context not found for this user"
        )
    
    ai_context.productivity_insights = insights
    ai_context.last_updated = datetime.utcnow()
    session.add(ai_context)
    session.commit()
    session.refresh(ai_context)
    return ai_context 