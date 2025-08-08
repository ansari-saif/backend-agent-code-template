import json
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from app.models.ai_context import AIContext
from app.schemas.ai_context import AIContextCreate, AIContextUpdate


def create_ai_context(session: Session, data: AIContextCreate) -> AIContext:
    existing = session.exec(select(AIContext).where(AIContext.user_id == data.user_id)).first()
    if existing:
        raise ValueError("AI context already exists for this user")

    if data.behavior_patterns:
        # validate JSON format
        json.loads(data.behavior_patterns)

    ctx = AIContext.model_validate(data)
    session.add(ctx)
    session.commit()
    session.refresh(ctx)
    return ctx


def list_ai_contexts(session: Session, skip: int = 0, limit: int = 100, user_id: Optional[str] = None) -> List[AIContext]:
    statement = select(AIContext)
    if user_id:
        statement = statement.where(AIContext.user_id == user_id)
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()


def get_ai_context(session: Session, context_id: int) -> Optional[AIContext]:
    return session.get(AIContext, context_id)


def update_ai_context(session: Session, context_id: int, update: AIContextUpdate) -> AIContext:
    ai_context = session.get(AIContext, context_id)
    if not ai_context:
        raise LookupError("AI context not found")
    data = update.model_dump(exclude_unset=True)
    if "behavior_patterns" in data and data["behavior_patterns"]:
        json.loads(data["behavior_patterns"])  # validate JSON
    for field, value in data.items():
        setattr(ai_context, field, value)
    ai_context.last_updated = datetime.utcnow()
    session.add(ai_context)
    session.commit()
    session.refresh(ai_context)
    return ai_context


def delete_ai_context(session: Session, context_id: int) -> None:
    ai_context = session.get(AIContext, context_id)
    if not ai_context:
        raise LookupError("AI context not found")
    session.delete(ai_context)
    session.commit()


def get_user_ai_context(session: Session, user_id: str) -> Optional[AIContext]:
    return session.exec(select(AIContext).where(AIContext.user_id == user_id)).first()


def upsert_behavior_patterns(session: Session, user_id: str, patterns: dict) -> AIContext:
    ai_context = get_user_ai_context(session, user_id)
    if not ai_context:
        ai_context = AIContext.model_validate(
            AIContextCreate(user_id=user_id, behavior_patterns=json.dumps(patterns))
        )
        session.add(ai_context)
    else:
        ai_context.behavior_patterns = json.dumps(patterns)
        ai_context.last_updated = datetime.utcnow()
        session.add(ai_context)
    session.commit()
    session.refresh(ai_context)
    return ai_context


def update_productivity_insights(session: Session, user_id: str, insights: str) -> AIContext:
    ai_context = get_user_ai_context(session, user_id)
    if not ai_context:
        raise LookupError("AI context not found for this user")
    ai_context.productivity_insights = insights
    ai_context.last_updated = datetime.utcnow()
    session.add(ai_context)
    session.commit()
    session.refresh(ai_context)
    return ai_context


