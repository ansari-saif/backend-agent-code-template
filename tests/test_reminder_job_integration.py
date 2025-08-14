import os
import json
from datetime import datetime, timedelta

import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool


@pytest.mark.asyncio
async def test_reminder_job_batched_notifications(monkeypatch):
    # Create isolated in-memory engine and tables
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Import models to ensure metadata populated
    from app.models.user import User  # noqa: F401
    from app.models.goal import Goal  # noqa: F401
    from app.models.task import Task  # noqa: F401
    from app.models.prompt import Prompt  # noqa: F401
    SQLModel.metadata.create_all(engine)

    # Patch reminder service to use this engine
    import app.services.reminder_service as rs
    monkeypatch.setattr(rs, "engine", engine, raising=True)

    # Prepare IST date/time windows
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(IST)
    due_time = (now_ist + timedelta(minutes=19)).time()
    today = now_ist.date()

    # Seed tasks due within next 30 minutes
    from app.models.task import Task, CompletionStatusEnum
    with Session(engine) as session:
        t1 = Task(
            user_id="u1",
            description="Prepare demo",
            completion_status=CompletionStatusEnum.PENDING,
            scheduled_for_date=today,
            scheduled_for_time=due_time,
        )
        t2 = Task(
            user_id="u2",
            description="Review PRs",
            completion_status=CompletionStatusEnum.PENDING,
            scheduled_for_date=today,
            scheduled_for_time=due_time,
        )
        session.add(t1)
        session.add(t2)
        session.commit()
        session.refresh(t1)
        session.refresh(t2)
        t1_id = t1.task_id
        t2_id = t2.task_id

    # Patch websocket connections with dummy receivers
    import app.api.v1.routes.websocket as ws

    class DummyWS:
        def __init__(self):
            self.messages = []

        async def send_text(self, text: str):
            self.messages.append(text)

    ws.connections.clear()
    ws.connections["u1"] = DummyWS()
    ws.connections["u2"] = DummyWS()

    # Do not mock Gemini; if GEMINI_API_KEY exists it will be used, otherwise fallback triggers

    # Run the async reminder job
    await rs.task_reminder_job()

    # Verify prompts persisted and notifications sent
    with Session(engine) as session:
        from sqlmodel import select
        from app.models.prompt import Prompt
        prompts = session.exec(select(Prompt)).all()
        assert len(prompts) == 2

    assert ws.connections["u1"].messages and json.loads(ws.connections["u1"].messages[0])["message"]
    assert ws.connections["u2"].messages and json.loads(ws.connections["u2"].messages[0])["message"]


