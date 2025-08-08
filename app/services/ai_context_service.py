from sqlmodel import Session, select
from datetime import datetime

from app.models.ai_context import AIContext
from app.schemas.ai_context import AIContextCreate, AIContextUpdate


def create_ai_context(session: Session, ai_context_data: AIContextCreate) -> AIContext:
    """Create a new AI context for a user."""
    ai_context = AIContext(**ai_context_data.model_dump())
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